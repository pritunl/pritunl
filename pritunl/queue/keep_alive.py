def _keep_alive_thread(self):
    messenger = Messenger()

    while True:
        time.sleep(self.ttl - 5)
        if self.queue_com.state in (COMPLETE, STOPPED):
            break
        response = self.collection.update({
            '_id': bson.ObjectId(self.id),
            'runner_id': self.runner_id,
        }, {'$set': {
            'ttl_timestamp': datetime.datetime.utcnow() + \
                datetime.timedelta(seconds=self.ttl),
        }})
        if response['updatedExisting']:
            logger.debug('Queue keep alive updated', 'queue',
                queue_id=self.id,
                queue_type=self.type,
            )

            messenger.publish('queue', [UPDATE, self.id])
        else:
            logger.debug('Queue keep alive lost reserve', 'queue',
                queue_id=self.id,
                queue_type=self.type,
            )

            self.queue_com.state_lock.acquire()
            try:
                self.queue_com.state = STOPPED
            finally:
                self.queue_com.state_lock.release()
            raise QueueStopped('Lost reserve, queue stopped', {
                'queue_id': self.id,
                'queue_type': self.type,
                })

    logger.debug('Queue keep alive thread ended', 'queue',
        queue_id=self.id,
        queue_type=self.type,
    )

def start_keep_alive(self):
    self.keep_alive_thread = threading.Thread(
        target=self._keep_alive_thread)
    self.keep_alive_thread.daemon = True
    self.keep_alive_thread.start()
