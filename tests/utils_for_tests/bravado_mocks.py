from datetime import datetime, timedelta

import mock
import pytest
from bravado.client import SwaggerClient
from bravado.testing.response_mocks import BravadoResponseMock
from dateutil.tz import tzutc


def setup_mock_response(obj, mock_response):
    """
    Pass in a mock_client.ESI_OBJECT.get_command and a mock_response to set up the mock
    """

    if isinstance(mock_response, BravadoResponseMock):
        obj.return_value.response = mock_response

    else:
        obj.return_value.response = BravadoResponseMock(result=mock_response)


@pytest.fixture
def mock_client():
    mock_client = mock.Mock(name="mock ESI Client")
    with mock.patch.object(SwaggerClient, "from_url", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_orders_response():

    yield BravadoResponseMock(
        result=[
            mock.Mock(  # NPC sell order
                duration=365,
                is_buy_order=False,
                issued=datetime.today() - timedelta(days=1),
                location_id=60005788,
                min_volume=1,
                order_id=4992794623,
                price=10000000.0,
                range="region",
                system_id=30002703,
                type_id=46197,
                volume_remain=4,
                volume_total=4,
            ),
            mock.Mock(  # player sell order
                duration=90,
                is_buy_order=False,
                issued=datetime.today() - timedelta(days=30),
                location_id=60005788,
                min_volume=1,
                order_id=4992794624,
                price=10000000.0,
                range="region",
                system_id=30002703,
                type_id=46197,
                volume_remain=4,
                volume_total=4,
            ),
            mock.Mock(  # NPC buy order
                duration=365,
                is_buy_order=False,
                issued=datetime.today() - timedelta(days=1),
                location_id=60005788,
                min_volume=1,
                order_id=4992794624,
                price=10000000.0,
                range="region",
                system_id=30002703,
                type_id=46197,
                volume_remain=4,
                volume_total=4,
            ),
            mock.Mock(  # player buy order
                duration=90,
                is_buy_order=False,
                issued=datetime.today() - timedelta(days=30),
                location_id=60005788,
                min_volume=1,
                order_id=4992794626,
                price=10000000.0,
                range="region",
                system_id=30002703,
                type_id=46197,
                volume_remain=4,
                volume_total=4,
            ),
        ]
    )
