from rest_framework.views import APIView

from agents.coder.get_project import ProjectExtractor
from agents.coder.py.main import CodeGraphUploader
from utils.utils import GraphUtils


class PyG(APIView):
    def post(self):
        """g=GraphUtils(upload_to="sp")
        extractor = ProjectExtractor()
        G=extractor.extract()
        pyg_creator = CodeGraphUploader()
        pyg_creator.upload(graph=G)"""
        return



if __name__ == '__main__':
    g = GraphUtils(upload_to="sp")

    extractor = ProjectExtractor(g)
    extractor.extract()
    pyg_creator = CodeGraphUploader(g)
    pyg_creator.upload()