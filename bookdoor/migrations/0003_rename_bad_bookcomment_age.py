# Generated by Django 3.2.5 on 2021-09-05 01:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookdoor', '0002_auto_20210904_1128'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bookcomment',
            old_name='bad',
            new_name='age',
        ),
    ]