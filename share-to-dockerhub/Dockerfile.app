# donelongo/geonode-app  — GeoNode/Django backend with CURRENT project code baked in.
# The dev stack mounts ./src over the image at runtime; for the boss (no source on
# disk) we bake the current backend into the image instead. No pip reinstall is
# needed because no new Python dependencies were added.
ARG BASE=my_geonode/geonode:4.4.2
FROM ${BASE}

# Overlay the current backend source (models, migrations, info_hub app, settings…)
COPY src /usr/src/my_geonode

WORKDIR /usr/src/my_geonode

# Patch a real upstream GeoNode migration bug: the original
# documents/migrations/0036_clean_document_thumbnails.py imports the live
# Document model (not the historical one), which picks up modeltranslation's
# title_am/om/ti fields added by a later migration. On a completely fresh,
# empty database this crashes migrate with "column ... title_am does not
# exist". This only happens when nothing has been restored into the database
# yet, so it can bite any from-scratch install. See patches/README for detail.
COPY share-to-dockerhub/patches/0036_clean_document_thumbnails.py /usr/local/lib/python3.10/dist-packages/geonode/documents/migrations/0036_clean_document_thumbnails.py
COPY share-to-dockerhub/patches/0006_dataset_migration.py /usr/local/lib/python3.10/dist-packages/importer/migrations/0006_dataset_migration.py
COPY share-to-dockerhub/patches/0007_align_resourcehandler_with_asset.py /usr/local/lib/python3.10/dist-packages/importer/migrations/0007_align_resourcehandler_with_asset.py

# Add missing translation-column migrations: modeltranslation adds am/om/ti
# fields to GeoNode's own core models (base, documents, layers, maps, groups,
# services) at the Python level, but the schema migrations to add those
# columns to Postgres were never generated for them (only for our own
# info_hub app). This only breaks on a from-scratch install where these
# columns genuinely never existed. Our restored bundle data already has
# these applied (marked --fake against a DB that already had the columns),
# so this is a no-op there and a real fix on a fresh install.
COPY share-to-dockerhub/patches/new_migrations/base_0093.py /usr/local/lib/python3.10/dist-packages/geonode/base/migrations/0093_license_description_am_license_description_om_and_more.py
COPY share-to-dockerhub/patches/new_migrations/documents_0039.py /usr/local/lib/python3.10/dist-packages/geonode/documents/migrations/0039_document_abstract_am_document_abstract_om_and_more.py
COPY share-to-dockerhub/patches/new_migrations/groups_0035.py /usr/local/lib/python3.10/dist-packages/geonode/groups/migrations/0035_groupcategory_name_am_groupcategory_name_om_and_more.py
COPY share-to-dockerhub/patches/new_migrations/layers_0045.py /usr/local/lib/python3.10/dist-packages/geonode/layers/migrations/0045_dataset_abstract_am_dataset_abstract_om_and_more.py
COPY share-to-dockerhub/patches/new_migrations/maps_0044.py /usr/local/lib/python3.10/dist-packages/geonode/maps/migrations/0044_map_abstract_am_map_abstract_om_map_abstract_ti_and_more.py
COPY share-to-dockerhub/patches/new_migrations/services_0055.py /usr/local/lib/python3.10/dist-packages/geonode/services/migrations/0055_service_description_am_service_description_om_and_more.py
COPY share-to-dockerhub/patches/new_migrations/upload_0040.py /usr/local/lib/python3.10/dist-packages/geonode/upload/migrations/0040_alter_uploadparallelismlimit_max_number.py
