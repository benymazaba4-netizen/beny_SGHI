import pytest


@pytest.mark.django_db
def test_health_endpoint(api_client):
    response = api_client.get('/api/v1/sante')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] in ('healthy', 'degraded', 'unhealthy')
    assert 'database_ok' in data


@pytest.mark.django_db
def test_api_docs_available(api_client):
    response = api_client.get('/api/v1/docs')
    assert response.status_code == 200
