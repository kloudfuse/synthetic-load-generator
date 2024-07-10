package io.omnition.loadgenerator.util;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Objects;
import java.util.Random;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

import io.omnition.loadgenerator.model.topology.ServiceRoute;
import io.omnition.loadgenerator.model.topology.ServiceTier;
import io.omnition.loadgenerator.model.topology.TagGenerator;
import io.omnition.loadgenerator.model.topology.TagSet;
import io.omnition.loadgenerator.model.topology.Topology;
import io.omnition.loadgenerator.model.trace.KeyValue;
import io.omnition.loadgenerator.model.trace.Reference;
import io.omnition.loadgenerator.model.trace.Reference.RefType;
import io.omnition.loadgenerator.model.trace.Service;
import io.omnition.loadgenerator.model.trace.Span;
import io.omnition.loadgenerator.model.trace.Trace;

public class TraceGenerator {
    private final Random random = new Random();
    private final Trace trace = new Trace();
    private Topology topology;

    private static final AtomicLong sequenceNumber = new AtomicLong(1);

    public static Trace generate(Topology topology, String rootServiceName, String rootRouteName, long endTimeMicros) {
        TraceGenerator gen = new TraceGenerator(topology);
        ServiceTier rootService = gen.topology.getServiceTier(rootServiceName);
        String instanceName = rootService.instances.get(gen.random.nextInt(rootService.instances.size()));
        Service service = new Service(rootService.serviceName, instanceName, rootService.getServiceLabels());
        Span rootSpan = gen.createSpanForServiceRouteCall(null, rootService, rootRouteName, endTimeMicros);
        rootSpan.service = service;
        gen.trace.rootSpan = rootSpan;
        gen.trace.addRefs();
        return gen.trace;
    }

    private TraceGenerator(Topology topology) {
        this.topology = topology;
    }

    private Span createSpanForServiceRouteCall(TagSet parentTagSet, ServiceTier serviceTier, String routeName, long endTimeMicros) {
        String instanceName = serviceTier.instances.get(
                random.nextInt(serviceTier.instances.size()));
        ServiceRoute route = serviceTier.getRoute(routeName);

        Span clientSpan = new Span();
        clientSpan.endTimeMicros = endTimeMicros;
        clientSpan.operationName = route.route;
        clientSpan.tags.add(KeyValue.ofStringType("span.kind", "client"));

        if (serviceTier.serviceType.equalsIgnoreCase("db") || serviceTier.serviceType.equalsIgnoreCase("external")) {
            TagSet routeTags = serviceTier.getTagSet(routeName);
            clientSpan.tags.addAll(getSpanTags(routeTags, parentTagSet));
            long ownDuration = TimeUnit.MILLISECONDS.toMicros(route.minLatencyMillis) + TimeUnit.MILLISECONDS.toMicros(this.random.nextInt(route.maxLatencyMillis));
            clientSpan.startTimeMicros = clientSpan.endTimeMicros - ownDuration;
            trace.addSpan(clientSpan);
            return clientSpan;
        }

        // send tags of serviceTier and serviceTier instance
        Service service = new Service(serviceTier.serviceName, instanceName, serviceTier.getServiceLabels());
        Span span = new Span();
        span.endTimeMicros = endTimeMicros;
        span.operationName = route.route;
        span.service = service;
        span.tags.add(KeyValue.ofLongType("load_generator.seq_num", sequenceNumber.getAndIncrement()));
        span.tags.add(KeyValue.ofStringType("span.kind", "server"));

        // Setup base tags
        span.setHttpMethodTag("GET");
        span.setHttpUrlTag("http://" + serviceTier.serviceName + routeName);
        // Get additional tags for this route, and update with any inherited tags
        TagSet routeTags = serviceTier.getTagSet(routeName);
        List<KeyValue> spanTags = getSpanTags(routeTags, parentTagSet);
        span.tags.addAll(spanTags);
        clientSpan.tags.addAll(spanTags);

        final AtomicLong minStartTime = new AtomicLong(endTimeMicros);
        if (span.isErrorSpan()) {
            // inject root cause error and terminate trace there
            span.markRootCauseError();
        } else {
            // no error, make downstream calls
            route.downstreamCalls.forEach((s, r) -> {
                long childEndTimeMicros = endTimeMicros - TimeUnit.MILLISECONDS.toMicros(random.nextInt(Math.max(route.minLatencyMillis, route.maxLatencyMillis)));
                ServiceTier childSvc = this.topology.getServiceTier(s);
                Span childSpan = createSpanForServiceRouteCall(routeTags, childSvc, r, childEndTimeMicros);
                childSpan.service = span.service;
                Reference ref = new Reference(RefType.CHILD_OF, span.id, childSpan.id);
                childSpan.refs.add(ref);
                minStartTime.set(Math.min(minStartTime.get(), childSpan.startTimeMicros));
                if (childSpan.isErrorSpan()) {
                    Integer httpCode = childSpan.getHttpCode();
                    if (httpCode != null) {
                        span.setHttpCode(httpCode);
                    }
                    span.markError();
                }
            });
        }
        long ownDuration = TimeUnit.MILLISECONDS.toMicros(route.minLatencyMillis) + TimeUnit.MILLISECONDS.toMicros(this.random.nextInt(route.maxLatencyMillis));
        span.startTimeMicros = minStartTime.get() - ownDuration;
        clientSpan.startTimeMicros = minStartTime.get() - ownDuration;
        if (parentTagSet != null) {
            Reference ref = new Reference(RefType.CHILD_OF, clientSpan.id, span.id);
            span.refs.add(ref);
            trace.addSpan(clientSpan);
        }
        trace.addSpan(span);
        if (parentTagSet != null) {
            return clientSpan;
        } else {
            return span;
        }
    }

    private static List<KeyValue> getSpanTags(TagSet routeTags, TagSet parentTagSet) {
        HashMap<String, Object> tagsToSet = new HashMap<>(routeTags.tags);
        for (TagGenerator tagGenerator : routeTags.tagGenerators) {
            tagsToSet.putAll(tagGenerator.generateTags());
        }
        if (parentTagSet != null && routeTags.inherit != null) {
            for (String inheritTagKey : routeTags.inherit) {
                Object value = parentTagSet.tags.get(inheritTagKey);
                if (value != null) {
                    tagsToSet.put(inheritTagKey, value);
                }
            }
        }

        return tagsToSet.entrySet().stream()
                .map(t -> {
                    Object val = t.getValue();
                    if (val instanceof String) {
                        return KeyValue.ofStringType(t.getKey(), (String) val);
                    }
                    if (val instanceof Double) {
                        return KeyValue.ofLongType(t.getKey(), ((Double) val).longValue());
                    }
                    if (val instanceof Boolean) {
                        return KeyValue.ofBooleanType(t.getKey(), (Boolean) val);
                    }
                    return null;
                })
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
    }
}
