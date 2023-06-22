import json
import random
from collections import defaultdict


def generateServiceInstanceName(serviceName, n):
    return serviceName + "-instance-" + str(n)


def generateCallGraph(serviceRoutes, numServices, fanOut, maxDepth):
    services = []
    nextLevel = 1
    numServicesPerLevel = int(numServices/maxDepth)
    numRoutesPerService = 2
    nextLevelRoutes = [(route, service) for route in range(0, numRoutesPerService) for service in range(0, numServicesPerLevel)]
    nextLevelRoutes.reverse()
    while nextLevel < maxDepth:
        nextServiceRoutes = {}
        servicesCreated = 0
        totalRoutes = 0
        for (service, routes) in serviceRoutes.items():
            routesJson = []
            routesGenerated = 0
            for route in routes:
                # while fanoutDone < fanOut and len(nextLevelRoutes):
                internalSpanRouteJson = {}
                clientSpanCallsJson = defaultdict(list) # dict of lists. Create routes from each list
                downStreamCallsJson = {}
                

                # Create rout from server to internal span
                internalSpanRoute = str(routesGenerated) + '-route-internal'
                internalSpanRouteJson[service] = internalSpanRoute


                # Create route from internal to client span
                clientSpanRoute = service + '-route-client' + '-' + str(routesGenerated)
                clientSpanCallsJson[service].append(clientSpanRoute)

                # Create route from client span to next service's server span
                (nextServiceRouteNum, nextServiceNum) = nextLevelRoutes.pop()
                nextService = 'service-' + str(nextLevel) + '-' + str(nextServiceNum)
                nextRoute = nextService + '-route-' + str(nextServiceRouteNum)
                downStreamCallsJson[nextService] = nextRoute
                if nextService not in nextServiceRoutes:
                    nextServiceRoutes[nextService] = {}
                nextServiceRoutes[nextService][nextRoute] = {}
                routesGenerated += 1


                # Add route from server to internal span
                routesJson.append(
                    {
                        'route': route,
                        'downstreamCalls': internalSpanRouteJson,
                        'maxLatencyMillis': random.randrange(10, 100),
                        'tagSets': [{
                            'tags': {
                                'span.kind': 'server',
                                'env': 'prod',
                            },
                            "tagGenerators":  [{"numTags":  4, "numVals":  5, "valLength": 8}]
                        }]
                    }
                )
                routeNum = 0
                # Add route from internal to client span. This has one downstream call.
                for (service, clientSpans) in clientSpanCallsJson.items():
                    for clientSpan in clientSpans:
                        routesJson.append(
                            {
                                'route': internalSpanRouteJson[service],
                                'downstreamCalls': {service: clientSpan},
                                'maxLatencyMillis': random.randrange(10, 100),
                                'tagSets': [{
                                    'tags': {
                                        'span.kind': 'internal',
                                        'env': 'prod',
                                    },
                                    "tagGenerators":  [{"numTags":  4, "numVals":  5, "valLength": 8}]
                                }]
                            }
                        )
                        routeNum += 1
                routeNum = 0
                for downStreamCall in downStreamCallsJson.items():
                    # Add route from client span to next service's server span. This has one downstream call.
                    routesJson.append(
                        {
                            'route': clientSpanCallsJson[service][routeNum],
                            'downstreamCalls': {service:downStreamCall[1]},
                            'maxLatencyMillis': random.randrange(10, 100),
                            'tagSets': [{
                                'tags': {
                                    'span.kind': 'client',
                                    'env': 'prod',
                                },
                                "tagGenerators":  [{"numTags":  4, "numVals":  5, "valLength": 8}]
                            }]
                        }
                    )
                    routeNum += 1
            services.append({
                'serviceName': service,
                'instances': [generateServiceInstanceName(service, n) for n in range(0, 5)],
                'routes': routesJson,
            })
            servicesCreated += 1

        nextLevelRoutes = [(route, service) for route in range(0, numRoutesPerService) for service in
                           range(0, numServicesPerLevel)]
        nextLevelRoutes.reverse()
        serviceRoutes = nextServiceRoutes
        nextLevel = nextLevel + 1

    # last level
    for (service, routes) in serviceRoutes.items():
        routesJson = []
        for route in routes:
            routesJson.append(
                {
                    'route': route,
                    'downstreamCalls': {},
                    'maxLatencyMillis': random.randrange(10, 100),
                    'tagSets': [{
                        'tags': {
                            'span.kind': 'service',
                            'env': 'prod',
                        },
                        "tagGenerators":  [{"numTags":  4, "numVals":  5, "valLength": 8}]
                    }]
                }
            )
        services.append({
            'serviceName': service,
            'instances': [generateServiceInstanceName(service, n) for n in range(0, 5)],
            'routes': routesJson,
        })
    return services



def main():
    root = {
        "service-0":
            {
                "route-0": {},
                "route-1": {},
                "route-2": {},
                "route-3": {},
                "route-4": {},
                "route-5": {},
                "route-6": {},
                "route-7": {},
                "route-8": {},
                "route-9": {}
            },
    }
    callGraph = generateCallGraph(root, 100, 10, 10)
    topology = {
        'topology': {
            'services': callGraph,
        },
        'rootRoutes': [
            {
                'service': service,
                'route': route,
                'tracesPerHour': 1000
            }
            for (service, routes) in root.items()
            for route in routes
        ]
    }
    print(json.dumps(topology, indent=2))


if __name__ == "__main__":
    main()
