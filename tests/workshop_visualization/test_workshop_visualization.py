ORIGIN_HEADER = { 'Origin': 'http://localhost:3000' }

def test_workshop_visualization_cors(client):
    response = client.options('/uvarc/api/workshops/attendance/data', headers=ORIGIN_HEADER)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)

def test_workshop_visualization_endpoint(client):
    response = client.get('/uvarc/api/workshops/attendance/data', headers=ORIGIN_HEADER)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_workshop_survey_visualization_cors(client):
    response = client.options('/uvarc/api/workshops/survey/data', headers=ORIGIN_HEADER)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)

def test_workshop_survey_visualization_endpoint(client):
    response = client.post('/uvarc/api/workshops/survey/data', headers=ORIGIN_HEADER)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
