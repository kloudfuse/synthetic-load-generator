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
                downStreamCallsJson = {}
                routesGenerated = 0
                while routesGenerated < fanOut and len(nextLevelRoutes) > 0:
                    (nextServiceRouteNum, nextServiceNum) = nextLevelRoutes.pop()
                    nextService = 'service-' + str(nextLevel) + '-' + str(nextServiceNum)
                    nextRoute = nextService + '-route-' + str(nextServiceRouteNum)
                    downStreamCallsJson[nextService] = nextRoute
                    if nextService not in nextServiceRoutes:
                        nextServiceRoutes[nextService] = {}
                    nextServiceRoutes[nextService][nextRoute] = {}
                    routesGenerated += 1
                routesJson.append(
                    {
                        'route': route,
                        'downstreamCalls': downStreamCallsJson,
                        'maxLatencyMillis': random.randrange(10, 100),
                        'tagSets': [{
                            'tags': {
                                'version': 'version-1',
                            }
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
                            'version': 'version-1',
                        }
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
                "route-1": {}
            },
    }
    callGraph = generateCallGraph(root, 12, 2, 4)
    topology = {
        'topology': {
            'services': callGraph,
        },
        'rootRoutes': [
            {
                'service': service,
                'route': route,
                'tracesPerHour': random.randrange(100, 10000)
            }
            for (service, routes) in root.items()
            for route in routes
        ]
    }
    print(json.dumps(topology, indent=2))


if __name__ == "__main__":
    main()
