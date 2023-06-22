* Generate topology file
  edit the parameters of generateCallGraph in generate_topology.py.
    numServices, fanOut, maxDepth
  edit 'tags' and/or 'tagGenerators' in routesJson as needed to get desired tags and cardinality
  `python3 generate_topology.py > file.json`
* Create configmap from any topology file you want
  `kubectl create cm trace-load-config --from-file=file-from-cfgmap=topologies/hipster-shop.json`
* Create deployment
  `kubectl apply -f Deployment.yaml`
