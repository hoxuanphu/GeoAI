"""Geographic exchange metadata; validation here does not run PROJ/GDAL."""
import math
from typing import Annotated, Literal

from pydantic import Field, JsonValue, model_validator

from .common import Contract, Identifier, PositiveInt, Sha256, Text, TimeRange, ValueModel


class CrsRef(ValueModel):
    format: Literal["authority", "wkt2", "projjson"]
    definition: Text
    revision: Text
    axis_order: tuple[Text, Text]
    unit: Text


class Wgs84Geometry(ValueModel):
    type: Literal["Polygon", "MultiPolygon"]
    coordinates: JsonValue

    @model_validator(mode="after")
    def closed_wgs84_rings(self):
        polygons = [self.coordinates] if self.type == "Polygon" else self.coordinates
        if not isinstance(polygons, list) or not polygons:
            raise ValueError("geometry must contain polygons")
        for polygon in polygons:
            if not isinstance(polygon, list) or not polygon:
                raise ValueError("polygon requires an exterior ring")
            for ring in polygon:
                if not isinstance(ring, list) or len(ring) < 4:
                    raise ValueError("ring requires at least four positions")
                for position in ring:
                    if not isinstance(position, list) or len(position) != 2:
                        raise ValueError("WGS84 position must be longitude, latitude")
                    if any(isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) for n in position):
                        raise ValueError("coordinates must be finite numbers")
                    if not (-180 <= position[0] <= 180 and -90 <= position[1] <= 90):
                        raise ValueError("coordinates outside WGS84 ranges")
                if ring[0] != ring[-1]:
                    raise ValueError("ring must be closed")
        return self


class ContentIdentity(ValueModel):
    kind: Literal["sha256", "provider_version", "etag_hint"]
    value: Text

    @model_validator(mode="after")
    def checksum_shape(self):
        if self.kind == "sha256":
            if len(self.value) != 64 or any(c not in "0123456789abcdef" for c in self.value):
                raise ValueError("sha256 requires 64 lowercase hexadecimal characters")
        return self


NoData = float | Literal["nan"] | None


class BandSpec(ValueModel):
    name: Identifier
    spectral_role: Text
    unit: Text
    scale: float = 1
    offset: float = 0
    nodata: NoData = None


class AssetRef(Contract):
    asset_id: Identifier
    provider: Identifier
    collection: Text
    product_profile_id: Identifier
    provider_scene_id: Text
    asset_key: Text
    processing_level: Text
    acquisition: TimeRange
    crs: CrsRef
    footprint: Wgs84Geometry
    bands: Annotated[tuple[BandSpec, ...], Field(min_length=1)]
    qa_profile_id: Identifier | None = None
    license_id: Identifier
    identity: ContentIdentity

    @model_validator(mode="after")
    def namespace_and_bands(self):
        if not self.asset_id.startswith(self.provider + ":"):
            raise ValueError("asset_id must use the provider namespace")
        if len({b.name for b in self.bands}) != len(self.bands):
            raise ValueError("band names must be unique")
        return self


class GridSpec(Contract):
    grid_id: Identifier
    crs: CrsRef
    # Affine [a,b,c,d,e,f]: x=a*col+b*row+c, y=d*col+e*row+f.
    # GDAL GeoTransform uses a different order: [c,a,b,f,d,e].
    affine: tuple[float, float, float, float, float, float]
    width: PositiveInt
    height: PositiveInt
    pixel_interpretation: Literal["area", "point"]
    data_kind: Literal["continuous", "categorical"]
    resampling: Literal["nearest", "mode", "bilinear", "cubic", "average"]
    output_dtype: Text
    nodata: NoData = None
    vertical_datum: Text | None = None

    @model_validator(mode="after")
    def invertible_and_label_safe(self):
        a, b, _, d, e, _ = self.affine
        determinant = a * e - b * d
        if determinant == 0 or not math.isfinite(determinant):
            raise ValueError("affine must be invertible and finite")
        if self.data_kind == "categorical" and self.resampling not in {"nearest", "mode"}:
            raise ValueError("categorical data requires label-preserving resampling")
        return self


class GridResource(ValueModel):
    resource_id: Identifier
    sha256: Sha256


class TransformSpec(Contract):
    transform_id: Identifier
    source_crs: CrsRef
    target_crs: CrsRef
    operation: Text
    grid_resources: tuple[GridResource, ...] = ()
    area_of_use: Wgs84Geometry
    tolerance_m: Annotated[float, Field(ge=0)]
    proj_version: Text
    proj_database_version: Text


class InputSnapshot(Contract):
    snapshot_id: Identifier
    project_id: Identifier
    aoi: Wgs84Geometry
    asset_ids: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    band_mapping: dict[Identifier, Text]
    qa_policy_id: Identifier
    acquisition: TimeRange
    temporal_selection: Literal["single_date", "composite", "time_series"]
    mosaic_recipe_id: Identifier | None = None
    grid_id: Identifier
    transform_ids: tuple[Identifier, ...] = ()
    dependency_ids: tuple[Identifier, ...] = ()
    retention_profile: Literal["references", "offline_pinned"]

    @model_validator(mode="after")
    def fixed_selection(self):
        if len(set(self.asset_ids)) != len(self.asset_ids):
            raise ValueError("asset IDs must be unique")
        if self.temporal_selection == "composite" and self.mosaic_recipe_id is None:
            raise ValueError("composite requires a mosaic recipe")
        return self
