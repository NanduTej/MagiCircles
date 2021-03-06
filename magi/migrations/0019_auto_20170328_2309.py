# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('magi', '0018_auto_20170326_0726'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='_cache_owner_preferences_i_status',
            field=models.CharField(max_length=12, null=True, choices=[(b'THANKS', b'Thanks'), (b'SUPPORTER', 'Player'), (b'LOVER', 'Super Player'), (b'AMBASSADOR', 'Extreme Player'), (b'PRODUCER', 'Master Player'), (b'DEVOTEE', 'Ultimate Player')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userlink',
            name='i_relevance',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='How often do you tweet/stream/post about BanG Dream! Girls Band Party?', choices=[(0, 'Never'), (1, 'Sometimes'), (2, 'Often'), (3, 'Every single day')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userpreferences',
            name='i_status',
            field=models.CharField(max_length=12, null=True, choices=[(b'THANKS', b'Thanks'), (b'SUPPORTER', 'Player'), (b'LOVER', 'Super Player'), (b'AMBASSADOR', 'Extreme Player'), (b'PRODUCER', 'Master Player'), (b'DEVOTEE', 'Ultimate Player')]),
            preserve_default=True,
        ),
    ]
