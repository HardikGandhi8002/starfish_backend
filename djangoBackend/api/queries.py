query = QueryModel.objects.filter(query_name = 'subtotal_classification_month').values('query').last()['query']
query_dict = dict(date_column='col1', location_filter=" api_SegmentData.integration_id= cast(13 as varchar) AND col7='Warrens'", start_d
    ...: ate='2022-11-01', end_date='2023-11-30', amount_column='col10', account_key_column = 'col2', company_id = '1')

query = QueryModel.objects.filter(query_name = 'fetch_locations').values('query').last()['query']




query = QueryModel.objects.filter(query_name ='wins_loses_query').values('query').last()['query']
{'date_column': 'col1',
 'location_filter': " api_SegmentData.integration_id= cast(13 as varchar) AND col7='Warrens'",
 'start_date': '2022-11-01',
 'end_date': '2023-11-30',
 'amount_column': 'col10',
 'account_key_column': 'col2',
 'company_id': '1',
 'integration_id': '13',
 'start_date_prev': '2021-11-01',
 'end_date_prev': '2022-11-01'}



 