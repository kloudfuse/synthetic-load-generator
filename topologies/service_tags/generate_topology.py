import json
import random
from dataclasses import dataclass

maxRoutes = 10

@dataclass
class Service:
    name: str
    instances: list
    routes: list
    downStreamCalls: list

def generateServiceInstanceName(serviceName, n):
    return serviceName + "-instance-" + str(n)

def generateRoutes(maxRoutes):
    return ["/route" + str(routeNum) for routeNum in range(1, maxRoutes)]

routes = generateRoutes(maxRoutes)

def generateServiceName(serviceNamePrefix, n):
    return serviceNamePrefix + "-" + str(n)

def generateService(serviceNamePrefix, n, routes):
    serviceName = generateServiceName(serviceNamePrefix, n)
    return Service(name=serviceName, routes=routes, downStreamCalls=[], instances=[generateServiceInstanceName(serviceName, m) for m in range(0, 10)])

def generateServices(serviceNamePrefix, nServices):
    return [generateService(serviceNamePrefix, serviceNum, routes) for serviceNum in range(1, nServices)]


def generateDownstreamCalls(services, maxCalls):
    for i in range(0, len(services)):
        for j in range(0, len(routes)):
            downStreamCalls = {}
            for k in range(0, maxCalls):
                i1 = random.randrange(i, len(services))
                j1 = random.randrange(0, len(routes))
                downstreamService = services[i1]
                downstreamRoute = routes[j1]
                downStreamCalls[downstreamService.name] = downstreamRoute
            services[j].downStreamCalls.append(downStreamCalls)


def toRouteJson(service, maxLatencyMillis=100):
    routeJson = []
    for i in range(0, len(service.routes)):
        routeJson.append({'route': service.routes[i], 'downstreamCalls': service.downStreamCalls[i], 'maxLatencyMillis': random.randrange(10, maxLatencyMillis)})
    return routeJson

def toTopologyJson(services, maxTracesPerHour=1000):
    servicesJson = [ { 'serviceName': service.name, 'instances': service.instances, 'routes': toRouteJson(service) } for service in services]
    rootService = services[0]
    return { 'topology': { 'services': servicesJson }, 'rootRoutes': [ {'service': rootService.name, 'route': route, 'tracesPerHour': random.randrange(100, maxTracesPerHour) } for route in rootService.routes] }

def main():
    services = generateServices("test", 10)
    generateDownstreamCalls(services, 5)
    print(services)
    print(json.dumps(toTopologyJson(services), indent=2))


if __name__ == "__main__":
    main()
