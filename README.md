relationpy
==========

library which encapsulate relational operations on iterator and has the basic functionality of Underscore js library

    payments = [
        {'id': 1, 'product': '1R', 'region': 'eu', 'vat': 'abc', 'amount': 100, 'currency': 'EUR'},
        {'id': 2, 'product': '1R', 'region': 'eu', 'amount': 200, 'currency': 'EUR'},
        {'id': 3, 'product': '3R', 'region': 'eu',  'amount': 200, 'currency': 'CZK'},
        {'id': 4, 'product': '3R', 'region': 'noneu', 'amount': 100, 'currency': 'EUR'},
        {'id': 5, 'product': '1R', 'region': 'noneu', 'vat': 'abc', 'amount': 100, 'currency': 'USD'},
    ]
    Relation(payments)\
        .extend(hasVat=lambda vat: bool(vat))\
        .groupByNames('product', 'region', 'hasVat')\
        .extend(
            name=lambda region, hasVat: region + ('-vat' if hasVat else ''),
            costEUR=lambda group: sum(o['amount'] for o in group if o['currency'] == 'EUR'),
            costCZK=lambda group: sum(o['amount'] for o in group if o['currency'] == 'CZK'),
            costUSD=lambda group: sum(o['amount'] for o in group if o['currency'] == 'USD'),
            vats=lambda group: ', '.join(o['vat'] for o in group if 'vat' in o),
        ).printTable(keys='name product costEUR costCZK costUSD vats')

produces

    name         product    costEUR    costCZK    costUSD    vats
    -------------------------------------------------------------
           eu         1R        200          0          0        
       eu-vat         1R        100          0          0     abc
    noneu-vat         1R          0          0        100     abc
           eu         3R          0        200          0        
        noneu         3R        100          0          0        
