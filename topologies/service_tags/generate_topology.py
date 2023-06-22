import json
import random


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
        for (service, routes) in serviceRoutes.items():
            routesJson = []
            for route in routes:
                clientSpanCallsJson = {}
                downStreamCallsJson = {}
                routesGenerated = 0
                while routesGenerated < fanOut and len(nextLevelRoutes) > 0:
                    # Create route from server to client span
                    clientSpanRoute = service + '-route-client'
                    clientSpanCallsJson[service] = clientSpanRoute

                    # Create route from client span to next service's server span
                    (nextServiceRouteNum, nextServiceNum) = nextLevelRoutes.pop()
                    nextService = 'service-' + str(nextLevel) + '-' + str(nextServiceNum)
                    nextRoute = nextService + '-route-' + str(nextServiceRouteNum)
                    downStreamCallsJson[nextService] = nextRoute
                    if nextService not in nextServiceRoutes:
                        nextServiceRoutes[nextService] = {}
                    nextServiceRoutes[nextService][nextRoute] = {}
                    routesGenerated += 1
                # Add route from server to client span
                routesJson.append(
                    {
                        'route': route,
                        'downstreamCalls': clientSpanCallsJson,
                        'maxLatencyMillis': random.randrange(10, 100),
                        'tagSets': [{
                            'tags': {
                                'span.kind': 'server',
                                'version': 'version-1',
                            },
                            "tagGenerators":  [{"numTags":  random.randrange(1, 5), "numVals":  random.randrange(1, 10), "valLength": random.randrange(4, 16)}]
                        }]
                    }
                )

                # Add route route from client span to next service's server span
                routesJson.append(
                    {
                        'route': clientSpanRoute,
                        'downstreamCalls': downStreamCallsJson,
                        'maxLatencyMillis': random.randrange(10, 100),
                        'tagSets': [{
                            'tags': {
                                'span.kind': 'client',
                                'version': 'version-1',
                                'env': 'prod',
                            },
                            "tagGenerators":  [{"numTags":  1, "numVals":  20, "valLength": 8}]
                        }]
                    }
                )
            services.append({
                'serviceName': service,
                'instances': [generateServiceInstanceName(service, n) for n in range(0, 5)],
                'routes': routesJson,
            })

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
                            'version': 'version-1',
                            'env': 'prod',
                        },
                        "tagGenerators":  [{"numTags":  1, "numVals":  20, "valLength": 8}]
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
                'tracesPerHour': 10000
            }
            for (service, routes) in root.items()
            for route in routes
        ]
    }
    print(json.dumps(topology, indent=2))


if __name__ == "__main__":
    main()
