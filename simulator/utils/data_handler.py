from utils.queue_handler import QueueHandler


class DataHandler:
    def __init__(self, upload_to, q_handler: QueueHandler or None =None):

        self.upload_to = upload_to
        self.history = {}
        self.schemas = {}
        self.q_handler=q_handler

    def save(self):
        pass



    def upsert_batch(self):


        return


    def add_history_entry(self, nid, ntype, attrs, timestep):
        """
        Adds all changes to a local history
        todo: directly upload here to spanner
        """
        print("Extend history")
        # Load local history
        if ntype not in self.history:
            self.history[ntype] = {}

        if not self.history[ntype].get(nid):
            self.history[ntype][nid] = {}

        # Include timestep key (for multiple updates / iteration
        if not self.history[ntype][nid].get(timestep):
            self.history[ntype][nid][timestep] = []

        self.history[ntype][nid][timestep].append(dict(id=nid, **{k: v for k, v in attrs.items() if k != "id"}))

        if len(self.history[ntype][nid][timestep]) > 10000:
            print("history limit exceeded -> push batch")
            # push updates todo: save history alltimes in BQ (after limit increase)
            self.q_handler.add_task(
                db_path=f"HIS_{ntype}/{nid}/{timestep}/",
                attrs=attrs
            )
        print("Finished history")


    def print_status(self):
        print(">>>STATUS")
        for k, v in self.schemas.items():
            print(f"Table {k}: \n{len(v['rows'])} rows \n")