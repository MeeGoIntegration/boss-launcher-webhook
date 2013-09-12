# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BuildService'
        db.create_table('app_buildservice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('namespace', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('apiurl', self.gf('django.db.models.fields.CharField')(unique=True, max_length=250)),
        ))
        db.send_create_signal('app', ['BuildService'])

        # Adding model 'WebHookMapping'
        db.create_table('app_webhookmapping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('repourl', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('branch', self.gf('django.db.models.fields.CharField')(default='master', max_length=100)),
            ('project', self.gf('django.db.models.fields.CharField')(default='pj:non-oss', max_length=250)),
            ('package', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('notify', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('build', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('obs', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.BuildService'])),
        ))
        db.send_create_signal('app', ['WebHookMapping'])

        # Adding model 'LastSeenRevision'
        db.create_table('app_lastseenrevision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mapping', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['app.WebHookMapping'])),
            ('revision', self.gf('django.db.models.fields.CharField')(max_length=250)),
        ))
        db.send_create_signal('app', ['LastSeenRevision'])


    def backwards(self, orm):
        # Deleting model 'BuildService'
        db.delete_table('app_buildservice')

        # Deleting model 'WebHookMapping'
        db.delete_table('app_webhookmapping')

        # Deleting model 'LastSeenRevision'
        db.delete_table('app_lastseenrevision')


    models = {
        'app.buildservice': {
            'Meta': {'object_name': 'BuildService'},
            'apiurl': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'namespace': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        'app.lastseenrevision': {
            'Meta': {'object_name': 'LastSeenRevision'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mapping': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['app.WebHookMapping']"}),
            'revision': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'app.webhookmapping': {
            'Meta': {'object_name': 'WebHookMapping'},
            'branch': ('django.db.models.fields.CharField', [], {'default': "'master'", 'max_length': '100'}),
            'build': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notify': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'obs': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['app.BuildService']"}),
            'package': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'project': ('django.db.models.fields.CharField', [], {'default': "'pj:non-oss'", 'max_length': '250'}),
            'repourl': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
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