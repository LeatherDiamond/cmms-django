from buildings.forms import BuildingForm

import pytest


@pytest.mark.django_db
def test_building_form_valid_data():
    form = BuildingForm(data={"name": "Building 1", "address": "123 Main St"})
    assert form.is_valid()


@pytest.mark.django_db
def test_building_form_empty_data():
    form = BuildingForm(data={})
    assert not form.is_valid()
    assert "name" in form.errors
    assert "address" in form.errors


@pytest.mark.django_db
def test_building_form_invalid_data():
    form = BuildingForm(data={"name": "", "address": "123 Main St"})
    assert not form.is_valid()
    assert "name" in form.errors
