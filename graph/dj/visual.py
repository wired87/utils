import asyncio
import os
from time import sleep

import networkx as nx
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework import serializers

from bm.settings import BASE_DIR
from rest_framework.views import APIView


def event_stream(html):
    while True:
        # Simulate live variable update
        yield html
        sleep(.025)

class S(serializers.Serializer):
    image_path = serializers.CharField(
        default="image_path",
        label="image_path",
    )

class GraphLookup(APIView):
    serializer_class=S





    def post(self, request, *args, **kwargs):
        image_path = request.data.get("image_path", r"C:\Users\wired\OneDrive\Desktop\BestBrain\qf_sim\physics\quantum_fields\nodes\qf\graphs\g.json")
        try:
            with open(r"C:\Users\wired\OneDrive\Desktop\BestBrain\qf_sim\physics\quantum_fields\nodes\qf\graphs\g.json", "r", encoding="utf-8") as f:
                html_content = f.read()

            return StreamingHttpResponse(html_content, content_type="text/html")
        except FileNotFoundError:
            return HttpResponse("File not found", status=404)
        except Exception as e:
            return HttpResponse(f"An error occurred: {e}", status=500)

"""StreamingHttpResponse(
                event_stream(html_content),
                content_type='text/event-stream'
            )"""
OPTIONS = {
    "autoResize": True,
    "height": '1000px',
    "width": '100%',
    "locale": 'en',
    "locales": {},
    "clickToUse": False,
    "configure": {},
    "edges": {
        "color": {
            "color": "white"
        },
        "arrows": {
            "to": {
                "enabled": False,
            }
        }
    },
    "nodes": {
        "borderWidthSelected": 21,
        "font": {
            "size": 30,
            "face": "verdana",
            "color": "white"
        },
        "shape": "circle",
        "color": {
            "background": "#34495e",
            "border": "#2c3e50",
            "highlight": {
                "background": "#5dade2",
                "border": "#2e86c1"
            }
        },
        "size": 30,
        "labelHighlightBold": True,
    },
    "groups": {},
    "layout": {},
    "interaction": {
        "hover": True,
        "tooltipDelay": 200,
        "selectable": True,
        "dragNodes": True,
        "dragView": True,
        "zoomView": True,
        "multiselect": True,
        "navigationButtons": False,
        "keyboard": {
            "enabled": False,
            "speed": {
                "x": 10,
                "y": 10,
                "zoom": 0.02
            },
            "bindToWindow": True
        }
    },
    "manipulation": {},
    "physics": {
        "barnesHut": {
            "gravitationalConstant": -4000,
            "centralGravity": 0.3,
            "springLength": 200,
            "springConstant": 0.04,
            "damping": 0.09
        },
        "forceAtlas2Based": {
            "gravitationalConstant": -4000,
            "springLength": 200,
        },
        "minVelocity": 0.75,
        "solver": "barnesHut",
        "stabilization": {
            "enabled": True,
            "iterations": 1000,
            "updateInterval": 50,
            "onlyDynamicEdges": False,
            "fit": True
        }
    }
}