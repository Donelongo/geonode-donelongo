#########################################################################
#
# Copyright (C) 2020 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
from drf_spectacular.utils import extend_schema

from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.mixins import AdvertisedListMixin
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import UserHasPerms
from geonode.base.api.views import ApiPresetsInitializer
from geonode.layers.api.exceptions import GeneralDatasetException, InvalidDatasetException, InvalidMetadataException
from geonode.layers.metadata import parse_metadata
from geonode.layers.models import Dataset
from geonode.maps.api.serializers import SimpleMapLayerSerializer, SimpleMapSerializer
from geonode.resource.utils import update_resource
from geonode.resource.manager import resource_manager
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from geonode.storage.manager import StorageManager

from .serializers import (
    DatasetSerializer,
    DatasetListSerializer,
    DatasetMetadataSerializer,
    DatasetTimeSeriesSerializer,
)
from .permissions import DatasetPermissionsFilter

from geonode import geoserver
from geonode.utils import check_ogc_backend

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.helpers import get_time_info

import logging

logger = logging.getLogger(__name__)


class DatasetViewSet(ApiPresetsInitializer, DynamicModelViewSet, AdvertisedListMixin):
    """
    API endpoint that allows layers to be viewed or edited.
    """

    http_method_names = ["get", "patch", "put"]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        UserHasPerms(perms_dict={"default": {"POST": ["base.add_resourcebase"]}}),
    ]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        ExtentFilter,
        DatasetPermissionsFilter,
    ]
    queryset = Dataset.objects.all().order_by("-created")
    serializer_class = DatasetSerializer
    pagination_class = GeoNodeApiPagination

    def get_serializer_class(self):
        if self.action == "list":
            return DatasetListSerializer
        if self.action == "timeseries_info":
            return DatasetTimeSeriesSerializer
        return DatasetSerializer

    def partial_update(self, request, *args, **kwargs):
        result = super().partial_update(request, *args, **kwargs)

        dataset = self.get_object()
        resource_manager.update(dataset.uuid, instance=dataset, notify=True),

        return result

    @extend_schema(
        request=DatasetMetadataSerializer,
        methods=["put"],
        responses={200},
        description="API endpoint to upload metadata file.",
    )
    @action(
        detail=False,
        url_path="(?P<pk>\d+)/metadata",  # noqa
        url_name="replace-metadata",
        methods=["put"],
        serializer_class=DatasetMetadataSerializer,
        permission_classes=[
            IsAuthenticated,
            UserHasPerms(perms_dict={"default": {"PUT": ["base.change_resourcebase_metadata"]}}),
        ],
    )
    def metadata(self, request, pk=None, *args, **kwargs):
        """
        Endpoint to upload ISO metadata
        Usage Example:

        import requests

        dataset_id = 1
        url = f"http://localhost:8080/api/v2/datasets/{dataset_id}/metadata"
        files=[
            ('metadata_file',('metadata.xml',open('/home/user/metadata.xml','rb'),'text/xml'))
        ]
        headers = {
            'Authorization': 'Basic dXNlcjpwYXNzd29yZA=='
        }
        response = requests.request("PUT", url, payload={}, files=files)

        cURL example:
        curl --location --request PUT 'http://localhost:8000/api/v2/datasets/{dataset_id}/metadata' \
        --form 'metadata_file=@/home/user/metadata.xml'
        """
        out = {}
        storage_manager = None
        if not self.queryset.filter(id=pk).exists():
            raise NotFound(detail=f"Dataset with ID {pk} is not available")
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            raise InvalidDatasetException(detail=serializer.errors)
        try:
            data = serializer.data.copy()
            if not data["metadata_file"]:
                raise InvalidMetadataException(detail="A valid metadata file must be specified")
            storage_manager = StorageManager(remote_files=data)
            storage_manager.clone_remote_files()
            file = storage_manager.get_retrieved_paths()
            metadata_file = file["metadata_file"]
            dataset = self.queryset.get(id=pk)
            try:
                dataset_uuid, vals, regions, keywords, _ = parse_metadata(open(metadata_file).read())
            except Exception:
                raise InvalidMetadataException(detail="Unsupported metadata format")
            if dataset_uuid and dataset.uuid != dataset_uuid:
                raise InvalidMetadataException(
                    detail="The UUID identifier from the XML Metadata, is different from the one saved"
                )
            try:
                updated_dataset = update_resource(dataset, metadata_file, regions, keywords, vals)
                updated_dataset.save()  # This also triggers the recreation of the XML metadata file according to the updated values
            except Exception:
                raise GeneralDatasetException(detail="Failed to update metadata")
            out["success"] = True
            out["message"] = ["Metadata successfully updated"]
            return Response(out)
        except Exception as e:
            raise e
        finally:
            if storage_manager:
                storage_manager.delete_retrieved_paths()

    @extend_schema(
        methods=["get"],
        responses={200: SimpleMapLayerSerializer(many=True)},
        description="API endpoint allowing to retrieve the MapLayers list.",
    )
    @action(detail=True, methods=["get"])
    def maplayers(self, request, pk=None, *args, **kwargs):
        dataset = self.get_object()
        resources = dataset.maplayers
        return Response(SimpleMapLayerSerializer(many=True).to_representation(resources))

    @extend_schema(
        methods=["get"],
        responses={200: SimpleMapSerializer(many=True)},
        description="API endpoint allowing to retrieve maps using the dataset.",
    )
    @action(detail=True, methods=["get"])
    def maps(self, request, pk=None, *args, **kwargs):
        dataset = self.get_object()
        resources = dataset.maps
        return Response(SimpleMapSerializer(many=True).to_representation(resources))

    @action(
        detail=True,
        url_path="timeseries",
        url_name="timeseries",
        methods=["get", "put"],
        permission_classes=[IsAuthenticated],
    )
    def timeseries_info(self, request, pk, *args, **kwards):
        """
        Endpoint for timeseries information

        url = "http://localhost:8080/api/v2/datasets/{dataset_id}/timeseries"

        cURL examples:
        GET method
        curl -X GET http://localhost:8000/api/v2/datasets/1/timeseries -u <username>:<password>

        PUT method
        curl -X PUT http://localhost:8000/api/v2/datasets/1/timeseries -u <username>:<password>
        -H "Content-Type: application/json" -d '{"has_time": true, "attribute": 4, "end_attribute": 5,
        "presentation": "DISCRETE_INTERVAL", "precision_value": 2, "precision_step": "months"}'
        """

        layer = get_object_or_404(Dataset, id=pk)

        if layer.supports_time is False:
            return JsonResponse({"message": "The time dimension is not supported for this dataset."}, status=200)

        if request.method == "GET":

            time_info = get_time_info(layer)
            serializer = DatasetTimeSeriesSerializer(data=time_info, context={"layer": layer})
            serializer.is_valid(raise_exception=True)
            serialized_time_info = serializer.data

            if layer.has_time is True and time_info is not None:
                serialized_time_info["has_time"] = layer.has_time
                return JsonResponse(serialized_time_info, status=200)
            else:
                return JsonResponse({"message": "No time information available."}, status=404)

        if request.method == "PUT":

            serializer = DatasetTimeSeriesSerializer(data=request.data, context={"layer": layer})
            serializer.is_valid(raise_exception=True)
            serialized_time_info = serializer.validated_data

            if serialized_time_info.get("has_time") is True:

                start_attr = (
                    layer.attributes.get(pk=serialized_time_info.get("attribute")).attribute
                    if serialized_time_info.get("attribute")
                    else None
                )
                end_attr = (
                    layer.attributes.get(pk=serialized_time_info.get("end_attribute")).attribute
                    if serialized_time_info.get("end_attribute")
                    else None
                )

                if start_attr is None and end_attr is None:
                    return JsonResponse(
                        {"message": "Please select at least one option between the attribute and end_attribute"},
                        status=200,
                    )

                # Save the has_time value to the database
                layer.has_time = True
                layer.save()

                resource_manager.exec(
                    "set_time_info",
                    None,
                    instance=layer,
                    time_info={
                        "attribute": start_attr,
                        "end_attribute": end_attr,
                        "presentation": serialized_time_info.get("presentation", None),
                        "precision_value": serialized_time_info.get("precision_value", None),
                        "precision_step": serialized_time_info.get("precision_step", None),
                        "enabled": serialized_time_info.get("has_time", False),
                    },
                )

                resource_manager.update(
                    layer.uuid,
                    instance=layer,
                    notify=True,
                )
                return JsonResponse({"message": "the time information data was updated successfully"}, status=200)
            else:
                # Save the has_time value to the database
                layer.has_time = False
                layer.save()

                return JsonResponse({"message": "The time dimension information for this layer was disabled"})
