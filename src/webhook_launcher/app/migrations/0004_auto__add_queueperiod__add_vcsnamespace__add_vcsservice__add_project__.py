# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'QueuePeriod'
        db.create_table('app_queueperiod', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('start_time', self.gf('django.db.models.fields.TimeField')(default=datetime.datetime(2014, 5, 23, 0, 0))),
            ('end_time', self.gf('django.db.models.fields.TimeField')(default=datetime.datetime(2014, 5, 23, 0, 0))),
            ('start_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('recurring', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('comment', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('app', ['QueuePeriod'])

        # Adding M2M table for field projects on 'QueuePeriod'
        m2m_table_name = 'app_queueperiod_projects'
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('queueperiod', models.ForeignKey(orm['app.queueperiod'], null=False)),
            ('project', models.ForeignKey(orm['app.project'], null=False))
        ))
        db.create_unique(m2m_table_name, ['queueperiod_id', 'project_id'])

        # Adding model 'VCSNameSpace'
        db.create_table('app_vcsnamespace', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.VCSService'])),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('app', ['VCSNameSpace'])

        # Adding model 'VCSService'
        db.create_table('app_vcsservice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('netloc', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('ips', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('app', ['VCSService'])

        # Adding model 'Project'
        db.create_table('app_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('obs', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.BuildService'])),
            ('official', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('allowed', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('app', ['Project'])

        # Adding unique constraint on 'Project', fields ['name', 'obs']
        db.create_unique('app_project', ['name', 'obs_id'])

        # Adding field 'BuildService.weburl'
        db.add_column('app_buildservice', 'weburl',
                      self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=250),
                      keep_default=False)

        # Adding field 'LastSeenRevision.tag'
        db.add_column('app_lastseenrevision', 'tag',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)

        # Adding field 'LastSeenRevision.handled'
        db.add_column('app_lastseenrevision', 'handled',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Removing unique constraint on 'Project', fields ['name', 'obs']
        db.delete_unique('app_project', ['name', 'obs_id'])

        # Deleting model 'QueuePeriod'
        db.delete_table('app_queueperiod')

        # Removing M2M table for field projects on 'QueuePeriod'
        db.delete_table('app_queueperiod_projects')

        # Deleting model 'VCSNameSpace'
        db.delete_table('app_vcsnamespace')

        # Deleting model 'VCSService'
        db.delete_table('app_vcsservice')

        # Deleting model 'Project'
        db.delete_table('app_project')

        # Deleting field 'BuildService.weburl'
        db.delete_column('app_buildservice', 'weburl')

        # Deleting field 'LastSeenRevision.tag'
        db.delete_column('app_lastseenrevision', 'tag')

        # Deleting field 'LastSeenRevision.handled'
        db.delete_column('app_lastseenrevision', 'handled')


    models = {
        'app.buildservice': {
            'Meta': {'object_name': 'BuildService'},
            'apiurl': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'namespace': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'weburl': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'})
        },
        'app.lastseenrevision': {
            'Meta': {'object_name': 'LastSeenRevision'},
            'handled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mapping': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['app.WebHookMapping']"}),
            'revision': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'app.project': {
            'Meta': {'unique_together': "(('name', 'obs'),)", 'object_name': 'Project'},
            'allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'obs': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['app.BuildService']"}),
            'official': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'app.queueperiod': {
            'Meta': {'object_name': 'QueuePeriod'},
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'default': 'datetime.datetime(2014, 5, 23, 0, 0)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['app.Project']", 'symmetrical': 'False'}),
            'recurring': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'start_time': ('django.db.models.fields.TimeField', [], {'default': 'datetime.datetime(2014, 5, 23, 0, 0)'})
        },
        'app.vcsnamespace': {
            'Meta': {'object_name': 'VCSNameSpace'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['app.VCSService']"})
        },
        'app.vcsservice': {
            'Meta': {'object_name': 'VCSService'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ips': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'netloc': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        'app.webhookmapping': {
            'Meta': {'object_name': 'WebHookMapping'},
            'branch': ('django.db.models.fields.CharField', [], {'default': "'master'", 'max_length': '100'}),
            'build': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'comment': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'debian': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2', 'blank': 'True'}),
            'dumb': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notify': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'obs': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['app.BuildService']"}),
            'package': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'project': ('django.db.models.fields.CharField', [], {'default': "'pj:non-oss'", 'max_length': '250'}),
            'repourl': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'token': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['app']
