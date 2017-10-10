# Stress Testing Pritunl

This documentation describes stress testing Pritunl. Python 2.7,
python-requests, go and docker are required.

### Emulate user connections

This test will emulate user connections to stress test the limits of Pritunls connection handler and web console. No actual VPN connections will be made in this test.

First in the Pritunl web console create a new organization then hold shift and click the green "Organization" label this will show the organization ID to the right.

Open the `add_test_users.py` file and copy the organization ID to the `ORG_ID` constant. Then set the `COUNT` to the number of users you want to create and set the `MONGO_URI` to your database. Once done run the script then refresh the web console and the test users should be added to the organization. These users contain test keys and cannot be used to connect to a server.

Create a test server with a network address of `10.165.0.0/16` and remove the `0.0.0.0/0` route. Once created attach the test organization to the server.

Before starting the test first stop any running vpn servers. Then in the terminal of the pritunl server run the command `pritunl set vpn.stress_test true`. Once this command is run start the test server.

Once started with stress_test mode the Pritunl server will emulate a connection for every user attached to the server. This test is a good representation of the maximum users your Pritunl and MongoDB servers would be able to handle without factoring in the limits of OpenVPN.

After the test is done run the command `pritunl set vpn.stress_test false`

### Test user connections

This test will create real user connections using a docker container for each client.

First edit the `get_test_names.py` and set the `COUNT` to the number of users you want to test. Then run the script and copy the list of user names into the Bulk Add Users for a new organization in the web console.

Create a test server with a network address of `10.154.0.0/16` and remove the `0.0.0.0/0` route. Once created attach the organization to the server and start the server. It is import that the public address for the server host is set to an address that docker containers will be able to access.

Then in the users page hold shift and click the green "Organization" label this will show the organization ID to the right. Open the `download_all_users.py` file and copy the organization ID to the `ORG_ID` constant. The set the `BASE_URL`, `API_TOKEN` and `API_SECRET` constants. The api key can be found in the settings. Then run the script. This will download all the user profiles to the `test_client/confs` directory for use by the docker container.

Once the profiles are downloaded run `cd test_client` then `docker build --rm -t test_client .`

Then edit `controller.go` and set the `count` constant to the number of users that you want to connect, this must be less then or equal to the number of users created.

Once done run the command `go run controller.go setup` this will create all the docker containers. Hitting ctrl-c will stop and remove the containers. After interrupting the running process wait for the remove process to complete. This will only start the docker containers no vpn connections will be made.

To connect all the clients run the command `go run controller.go start`.

To disconnect all the clients run the command `go run controller.go stop`.

To run a bandwidth test first setup an http server on port 8000 on the Pritunl server. Running `go get github.com/pacur/httpserver` will get a simple golang file server. Then create a test file from `/dev/urandom` or download one from [cachefly](http://cachefly.cachefly.net/speedtest/). Name the test file `test` and run `httpserver` to start the http server. The test file should be available at `http://localhost:8000/test`. Once setup run the command `go run controller.go download`. This will trigger all the clients to download the test file at the same time.

For debugging the handlers `http://localhost:4000/output` and `http://localhost:4000/router` are available. The port number should be `4000` + the user number, `user_0064` will have a port of `4064`. These handles will show the openvpn process output and display the routing table. The commands above such as `http://localhost:4000/ping` can also be run individually using the urls this will also show the output of the command.
