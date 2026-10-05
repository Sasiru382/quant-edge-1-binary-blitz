import pytest
from src import data

SAMPLE = '''Description
  Average Value Weighted Returns -- Daily
,Cnsmr,Manuf,HiTec,Hlth,Other
20060103,1,2,3,4,5
20060104,0,-1,-2,0,0

  Average Equal Weighted Returns -- Daily
,Cnsmr,Manuf,HiTec,Hlth,Other
20060103,99,99,99,99,99
'''

def test_first_value_weighted_section_and_percent_scaling():
    result = data.parse_returns(SAMPLE)
    assert list(result.columns) == ['HiTec', 'Manuf']
    assert result.iloc[0].tolist() == [0.03, 0.02]
    assert result.iloc[1].tolist() == [-0.02, -0.01]
    assert len(result) == 2

@pytest.mark.parametrize('value', ['-99.99', '-999', 'nan', '-101', 'inf'])
def test_invalid_source_returns_rejected(value):
    with pytest.raises(ValueError, match='invalid|sentinel'):
        data.parse_returns(SAMPLE.replace('20060103,1,2,3,4,5', f'20060103,1,2,{value},4,5'))

def test_duplicates_rejected():
    with pytest.raises(ValueError, match='duplicate'):
        data.parse_returns(SAMPLE.replace('20060104', '20060103'))


def test_data_audit_covers_observed_rows_extrema_and_absent_weekdays():
    audit = data.audit_returns(data.parse_returns(SAMPLE), '2006-01-04')
    assert audit['rows'] == 2
    assert audit['missing_values'] == 0
    assert audit['duplicate_dates'] == 0
    assert audit['train_rows'] == 1
    assert audit['test_rows'] == 1
    assert audit['sector_extrema']['HiTec']['min'] == -.02
    assert audit['sector_extrema']['HiTec']['max_date'] == '2006-01-03'
    assert audit['absent_weekdays_between_observed_endpoints'] == 0
