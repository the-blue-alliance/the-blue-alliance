import webapp2
import logging


class SubscriptionWorkerHandler(webapp2.RequestHandler):

    @staticmethod
    def task_queue():
        from google.appengine.api import taskqueue
        return taskqueue.Queue('tbans-update-subscriptions')

    """
    Push queue handler - we notify the worker via the push queue to pull tasks for a tag in the pull queue

    Task payload for the push queue *must* have a `tag`.
    """
    def post(self):
        from tbans.utils.validation_utils import validate_is_string
        tag = self.request.get('tag')
        validate_is_string(tag=tag)

        logging.info('Handling tasks for tag: {}'.format(tag))

        subscription_queue = SubscriptionWorkerHandler.task_queue()

        # Fetch "all" tasks from our task queue with the same tag. We'll only process once per tag, but we
        # use this to drain the queue, so we don't handle back-to-back requests when we don't need to do anything.
        # This is an optimization to cut down on the number of upstream status requests we make.
        # Note: This can throw - but if it throws, that's fine. We'll retry our task via the push queue later.
        tasks = subscription_queue.lease_tasks_by_tag(180, 1000, tag=tag, deadline=60)
        # If we don't have any tasks to handle - that's fine.
        if not tasks:
            return

        # Purge all but one task - we'll re-queue this single task if we fail, as opposed to re-queueing all tasks.
        task = tasks[0]
        tasks.remove(task)
        subscription_queue.delete_tasks(tasks)

        # Wrap everything in a try/catch - if we fail we need to un-lease our tasks
        try:
            import json
            payload = json.loads(task.payload)
            user_id = payload['user_id']
            token = payload.get('token', None)

            from tbans.controllers.subscription_controller import SubscriptionController

            success = True
            if token:
                logging.info('Dispatching update_token')
                # Subscribe/unsubscribe for the token.
                success = SubscriptionController.update_token(user_id, token)
            else:
                logging.info('Dispatching update_subscriptions')
                # Dispatch an update for all devices.
                success = SubscriptionController.update_subscriptions(user_id)

            logging.info('success: {}'.format(success))
            if success:
                subscription_queue.delete_tasks([task])
            else:
                subscription_queue.modify_task_lease(task, 0)
                self.response.set_status(500)
        except:
            subscription_queue.modify_task_lease(task, 0)
            raise


app = webapp2.WSGIApplication([
    ('/notify_subscription_worker', SubscriptionWorkerHandler)
])
