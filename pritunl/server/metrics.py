
class ServerMetrics(object):
    def __init__(self):
        self.metrics_allocated = {}
        self.metrics_server_map = {}

    def add_missing_metric(self, network_key, server_id):
        metrics = self.metrics_allocated.get(network_key, [])
        if len(metrics) == 0:
            self.metrics_allocated[network_key] = [1]
            self.metrics_server_map[server_id] = (network_key, 1)
            return 1

        m = max(metrics)

        missing = sorted(set(range(1, m)).difference(metrics))

        if len(missing) == 0:
            metrics.append(m + 1)
            self.metrics_allocated[network_key] = sorted(metrics)
            self.metrics_server_map[server_id] = (network_key, m + 1)
            return (m + 1)
        else:
            metrics.append(missing[0])
            self.metrics_allocated[network_key] = sorted(metrics)
            self.metrics_server_map[server_id] = (network_key, missing[0])
            return missing[0]

    def del_stopped_metric(self, server_id):
            network_key, metric = self.metrics_server_map[server_id]
            metrics = self.metrics_allocated[network_key]

            metrics.remove(metric)

            if len(metrics) == 0:
                del self.metrics_allocated[network_key]

            del self.metrics_server_map[server_id]
