import logging
from django.contrib import admin, messages
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from breathecode.admissions.admin import CohortAdmin
from breathecode.utils.admin import change_field
from .models import Asset, AssetTechnology, AssetAlias, AssetErrorLog
from .tasks import async_sync_with_github, async_test_asset
from .actions import sync_with_github, get_user_from_github_username, test_asset

logger = logging.getLogger(__name__)


def add_gitpod(modeladmin, request, queryset):
    assets = queryset.update(gitpod=True)


add_gitpod.short_description = 'Add GITPOD flag (to open on gitpod)'


def remove_gitpod(modeladmin, request, queryset):
    assets = queryset.update(gitpod=False)


remove_gitpod.short_description = 'Remove GITPOD flag'


def make_external(modeladmin, request, queryset):
    result = queryset.update(external=True)


make_external.short_description = 'Make it an EXTERNAL resource (new window)'


def make_internal(modeladmin, request, queryset):
    result = queryset.update(external=False)


make_internal.short_description = 'Make it an INTERNAL resource (same window)'


def pull_from_github(modeladmin, request, queryset):
    queryset.update(sync_status='PENDING')
    assets = queryset.all()
    for a in assets:
        async_sync_with_github.delay(a.slug, request.user.id)
        # sync_with_github(a.slug)  # uncomment for testing purposes


def make_me_author(modeladmin, request, queryset):
    assets = queryset.all()
    for a in assets:
        a.author = request.user
        a.save()


def get_author_grom_github_usernames(modeladmin, request, queryset):
    assets = queryset.all()
    for a in assets:
        authors = get_user_from_github_username(a.authors_username)
        if len(authors) > 0:
            a.author = authors.pop()
            a.save()


def make_me_owner(modeladmin, request, queryset):
    assets = queryset.all()
    for a in assets:
        a.owner = request.user
        a.save()


def test_asset_integrity(modeladmin, request, queryset):
    queryset.update(test_status='PENDING')
    assets = queryset.all()
    for a in assets:
        async_test_asset.delay(a.slug)


class AssessmentFilter(admin.SimpleListFilter):

    title = 'Associated Assessment'

    parameter_name = 'has_assessment'

    def lookups(self, request, model_admin):

        return (
            ('yes', 'Has assessment'),
            ('no', 'No assessment'),
        )

    def queryset(self, request, queryset):

        if self.value() == 'yes':
            return queryset.filter(assessment__isnull=False)

        if self.value() == 'no':
            return queryset.filter(assessment__isnull=True)


# Register your models here.
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    search_fields = ['title', 'slug', 'author__email', 'url']
    list_display = ('slug', 'title', 'current_status', 'lang', 'asset_type', 'techs', 'url_path')
    list_filter = ['asset_type', 'status', 'lang', AssessmentFilter]
    raw_id_fields = ['author', 'owner']
    actions = [
        test_asset_integrity,
        add_gitpod,
        remove_gitpod,
        pull_from_github,
        make_me_author,
        make_me_owner,
        get_author_grom_github_usernames,
    ] + change_field(['DRAFT', 'UNNASIGNED', 'OK'], name='status')

    def url_path(self, obj):
        return format_html(f"""
            <a rel='noopener noreferrer' target='_blank' href='{obj.url}'>github</a> |
            <a rel='noopener noreferrer' target='_blank' href='/v1/registry/asset/preview/{obj.slug}'>preview</a>
        """)

    def current_status(self, obj):
        colors = {
            'PUBLISHED': 'bg-success',
            'OK': 'bg-success',
            'ERROR': 'bg-error',
            'WARNING': 'bg-warning',
            None: 'bg-warning',
            'DRAFT': 'bg-error',
            'PENDING_TRANSLATION': 'bg-error',
            'PENDING': 'bg-warning',
            'WARNING': 'bg-warning',
            'UNASSIGNED': 'bg-error',
            'UNLISTED': 'bg-warning',
        }
        return format_html(
            f"""<table><tr><td style='font-size: 10px !important;'>Publish</td><td style='font-size: 10px !important;'>Synch</td><td style='font-size: 10px !important;'>Test</td></tr>
        <td><span class='badge {colors[obj.status]}'>{obj.status}</span></td>
        <td><span class='badge {colors[obj.sync_status]}'>{obj.sync_status}</span></td>
        <td><span class='badge {colors[obj.test_status]}'>{obj.test_status}</span></td>
        </table>""")

    def techs(self, obj):
        return ', '.join([t.slug for t in obj.technologies.all()])


def merge_technologies(modeladmin, request, queryset):
    technologies = queryset.all()
    target_tech = None
    for t in technologies:
        # skip the first one
        if target_tech is None:
            target_tech = t
            continue

        for a in t.asset_set.all():
            a.technologies.add(target_tech)
        t.delete()


# Register your models here.
@admin.register(AssetTechnology)
class AssetTechnologyAdmin(admin.ModelAdmin):
    search_fields = ['title', 'slug']
    list_display = ('slug', 'title')
    actions = (merge_technologies, )


@admin.register(AssetAlias)
class AssetAliasAdmin(admin.ModelAdmin):
    search_fields = ['slug']
    list_display = ('slug', 'asset', 'created_at')
    raw_id_fields = ['asset']


def make_alias(modeladmin, request, queryset):
    errors = queryset.all()
    for e in errors:
        if e.status_code != 404:
            messages.error(
                request,
                f'Error: You can only make alias for 404 errors and {e.slug} error was {e.status_code}')

        if e.asset is None:
            messages.error(
                request,
                f'Error: Cannot make alias to fix error {e.slug} ({e.id}), please assign asset before trying to fix it'
            )

        else:
            alias = AssetAlias.objects.filter(slug=e.slug).first()
            if alias is None:
                alias = AssetAlias(slug=e.slug, asset=e.asset)
                alias.save()
                e.status = 'FIXED'
                e.save()
                continue

            if alias.asset.id != e.asset.id:
                messages.error(request,
                               f'Slug {slug} already exists for a different asset {alias.asset.asset_type}')


@admin.register(AssetErrorLog)
class AssetErrorLogAdmin(admin.ModelAdmin):
    search_fields = ['slug', 'user__email', 'user_first_name', 'user_last_name']
    list_display = ('slug', 'current_status', 'user', 'created_at', 'asset')
    raw_id_fields = ['user', 'asset']
    actions = [make_alias]

    def current_status(self, obj):
        colors = {
            'FIXED': 'bg-success',
            'ERROR': 'bg-error',
            'IGNORED': '',
            None: 'bg-warning',
        }
        return format_html(
            f'<span class="badge d-block {colors[obj.status]}">{obj.status} {obj.status_code}</span>')
