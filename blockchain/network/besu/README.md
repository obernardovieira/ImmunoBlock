
By following [this tutorial](https://besu.hyperledger.org/en/latest/Tutorials/Private-Network/Create-Private-Clique-Network/), the developer must have all the information to get the three nodes running. SOme steps aren't needed, such as the folder generation, genesis files and node keys.

Having said that, it's only necessary to start the network. Remember, according to the tutorial, only the first node is minnig and the other two are receiving.

Now, it's only necessary to start the nodes.

Form node1 folder
`besu --data-path=data --genesis-file=../cliqueGenesis.json --network-id 123 --rpc-http-enabled --rpc-http-api=ETH,NET,CLIQUE --host-whitelist="*" --rpc-http-cors-origins="all"`

From node2 folder
`besu --data-path=data --genesis-file=../cliqueGenesis.json --bootnodes=<Node-1 Enode URL> --network-id 123 --p2p-port=30304 --rpc-http-enabled --rpc-http-api=ETH,NET,CLIQUE --host-whitelist="*" --rpc-http-cors-origins="all" --rpc-http-port=8546`

From node3 folder
`besu --data-path=data --genesis-file=../cliqueGenesis.json --bootnodes=<Node-1 Enode URL> --network-id 123 --p2p-port=30305 --rpc-http-enabled --rpc-http-api=ETH,NET,CLIQUE --host-whitelist="*" --rpc-http-cors-origins="all" --rpc-http-port=8547`

Node-1 Enode URL in printed on the console once it starts running. Just copy it. It should always be the same, even if you stop the node and start again.
