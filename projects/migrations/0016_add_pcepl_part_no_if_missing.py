from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0015_ascn'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE projects_project ADD COLUMN IF NOT EXISTS pcepl_part_no varchar(100);",
            reverse_sql="ALTER TABLE projects_project DROP COLUMN IF EXISTS pcepl_part_no;"
        ),
    ]
