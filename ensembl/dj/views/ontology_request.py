from rest_framework.views import APIView


class OntologyToGenes(APIView):


    def post(self, request, *args, **kwargs):
        go_terms = request.data.get('go_terms')


        """
        BEFORE ´:
        -> prompt to go-terms
        
        HERE:
        async task : 
        -> https://api.geneontology.org/api/bioentity/function/GO%3A0044598/genes?taxon=NCBITaxon%3A9606&relationship_type=involved_in&start=0&rows=100
        -> uniprot = Gene name 
        -> ens api sequence + info 
        ==============================
        Free playground in startup webpage
        """

