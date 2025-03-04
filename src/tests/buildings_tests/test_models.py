import pytest


@pytest.mark.django_db
def test_create_building(building_factory):
    building = building_factory()
    assert building.name == "Building 1"
    assert building.address == "123 Main St"


@pytest.mark.django_db
def test_building_str(building_factory):
    building = building_factory()
    assert str(building) == "Building 1"
