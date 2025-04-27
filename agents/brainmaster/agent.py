class RARAgent:
    def __init__(self, model):
        self.model = model
        self.behavior_roles = {
            "gather_info": self.gather_information,
            "check_neighbors": self.check_neighbor_embedding,
            "redirect": self.redirect_request,
            "adapt_input": self.adapt_input_data
        }

    def act(self, role, data):
        """Decides how the agent should behave based on assigned roles"""
        if role in self.behavior_roles:
            return self.behavior_roles[role](data)
        else:
            return "Invalid Role"

    def gather_information(self, query):
        """Simulate gathering additional information"""
        return f"Searching for extra details on: {query}"

    def check_neighbor_embedding(self, node_id):
        """Simulate checking neighbors' embeddings"""
        return f"Fetching neighbors' embeddings for: {node_id}"

    def redirect_request(self, node_id):
        """Redirect processing to another node"""
        return f"Redirecting request to closest node near {node_id}"

    def adapt_input_data(self, input_data):
        """Modify input for better predictions"""
        return f"Adapting input data: {input_data}"
