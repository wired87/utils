import os
from typing import List

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework.views import APIView

from dashboard.models import UserModel


@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class RunAgent(APIView):



    def build_docker_file(
            self,
            urls,
            project_dir="/agents/data_agent/docker/",
            output_filename="Dockerfile",

    ):














            dockerfile_content = f"""
            # AWS ###

            FROM public.ecr.aws/amazonlinux/amazonlinux:latest
            
            # Install dependencies
            RUN yum update -y && \
             yum install -y httpd
            
            # Install apache and write hello world message
            RUN echo 'Hello World!' > /var/www/html/index.html
            
            # Configure apache
            RUN echo 'mkdir -p /var/run/httpd' >> /root/run_apache.sh && \
             echo 'mkdir -p /var/lock/httpd' >> /root/run_apache.sh && \
             echo '/usr/sbin/httpd -D FOREGROUND' >> /root/run_apache.sh && \
             chmod 755 /root/run_apache.sh
            
            EXPOSE 80
            
            CMD /root/run_apache.sh
            
            # MAIN ###
            FROM --platform=linux/amd64 python:3.10 AS build \n
            WORKDIR "/app"
            COPY . /agents/data_agent/docker/
            RUN pip install --no-cache-dir -r r.txt
            CMD ["python", "main.py"]
            """.strip()

            output_path = os.path.join(project_dir, output_filename)
            with open(output_path, "w") as dockerfile:
                dockerfile.write(dockerfile_content)

            print(f"Dockerfile created at: {output_path}")

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        user = UserModel.objects.get(email=email)
        print("USER EXIST.:", user)
        if not user:
            return JsonResponse(
                {
                    'status_code': 21,
                    "message": "Could not send the confirmation Email. Please try again or contact the support"
                }
            )
        urls:List = request.data.get("urls")

        # build docker with urls as paraams
        self.build_docker_file(urls=urls,)
        return JsonResponse({"status": "JOB_ACCEPTED"})

