# coding=utf-8
'''
Test Kata's web user interface with Pylons WSGI application.
'''
import copy
import json

from ckanext.harvest import model as harvest_model
from lxml import etree

import ckan.model as model
import ckanext.kata.model as kata_model
from ckan.logic import get_action, NotAuthorized
from ckan.tests.legacy import url_for
from ckanext.kata import settings, utils
from ckanext.kata.tests.functional import KataWsgiTestCase
from ckanext.kata.tests.test_fixtures.unflattened import TEST_DATADICT, TEST_ORGANIZATION_COMMON
from ckanext.kata.controllers import ContactController
from ckan.lib.create_test_data import CreateTestData
from ckan.model import user as user_model
import ckanapi



from nose.tools import raises


class TestPages(KataWsgiTestCase):
    """
    Simple tests to see that pages render properly.
    """

    def test_group_page(self):
        """
        Test that help page is found and rendered.
        """
        offset = url_for('/group')
        res = self.app.get(offset)
        assert res.status == 200, 'Wrong HTTP status code (expecting 200)'
        assert len(etree.fromstring(res.body, parser=self.html_parser))

    def test_harvest_page(self):
        res = self.app.get('/harvest', extra_environ={})
        assert res.status == 200, 'Wrong HTTP status code (expecting 200)'
        assert len(etree.fromstring(res.body, parser=self.html_parser))

    def test_dataset_page(self):
        offset = url_for('/dataset')
        res = self.app.get(offset)
        assert res.status == 200, 'Wrong HTTP status code (expecting 200)'
        assert len(etree.fromstring(res.body, parser=self.html_parser))

    def test_urnexport_page(self):
        offset = url_for('/urnexport')
        res = self.app.get(offset)
        assert res.status == 200, 'Wrong HTTP status code (expecting 200)'
        assert len(etree.fromstring(res.body, parser=self.html_parser))

    def test_organization_page(self):
        offset = url_for('/organization')
        res = self.app.get(offset)
        assert res.status == 200, 'Wrong HTTP status code (expecting 200)'
        assert len(etree.fromstring(res.body, parser=self.html_parser))


class TestResources(KataWsgiTestCase):
    """
    Test that resources are handled properly in WUI.
    """

    # def test_data_and_resources_not_rendered(self):
    #     """
    #     A package with no resources should not render Data and Resources section
    #     """
    #     offset = url_for(controller='package', action='read', id=u'warandpeace')
    #     res = self.app.get(offset)
    #     assert '<section id="dataset-resources"' not in res, \
    #         'A package with no resources should not render Data and Resources section'
    #
    # def test_data_and_resources_rendered(self):
    #     """
    #     A package with resources should render Data and Resources section
    #     """
    #     offset = url_for(controller='package', action='read', id=u'annakarenina')
    #     res = self.app.get(offset)
    #     assert '<section id="dataset-resources"' in res, \
    #         'A package with resources should render Data and Resources section'

    def test_resource_read_redirect(self):
        """
        resource_read should redirect to dataset page.
        """
        model.repo.new_revision()
        model.Session.commit()
        res_id = None
        pkg = model.Package.get(u'annakarenina')
        pkg.name = utils.pid_to_name(pkg.id)
        model.Package.save(pkg)
        for resource in pkg.resources:
            if 'Full text.' in resource.description:
                model.repo.new_revision()
                resource.resource_type = settings.RESOURCE_TYPE_DATASET
                model.Session.commit()
                res_id = resource.id

        offset = '/en' + url_for(controller='package', action='resource_read',
                                 id=pkg.id, resource_id=res_id)

        extra_environ = {'REMOTE_USER': 'tester'}
        result = self.app.get(offset, extra_environ=extra_environ)

        # Redirect should redirect to dataset page
        result = result.follow()

        assert result.body.count('Full text.') == 0
        assert len(etree.fromstring(result.body, parser=self.html_parser))

        # resources_obj = etree.lxml.etree.fromstring(result.body).xpath("//u:identifier", namespaces=self.namespaces)
        # with open('/var/www/foo.txt', mode='wt') as f:
        #     f.write(result.body)
        # resources_obj = etree.fromstring(result.body).xpath("//div[div[text()='Files']]", namespaces=self.namespaces)
        # res_table = resources_obj.xpath("/div/table/tbody")

        # import pprint
        # pprint.pprint(dir(res_table))

    #         assert 'Full text.' in result.body

    # regex = re.compile(r'<a.*href.*>.*Edit\w*</a>')
    # assert not regex.search(result.body), "%r" % result.body

    # assert 'Edit Profile' in result.body    # Sanity check


class TestContactForm(KataWsgiTestCase):
    '''
    Test dataset contact form
    '''

    def test_contact_controller_no_user(self):
        """
        Test that we get a redirect when there is no user
        """
        offset = url_for("/contact/warandpeace")
        res = self.app.get(offset)
        assert res.status == 200, 'Everyone is allowed to contact'

    def test_contact_controller_user_logged_in(self):
        '''
        Test that we get the contact form when user is logged in

        Note: Form should probably be only visible if the dataset can be requested via the form?
        '''

        extra_environ = {'REMOTE_USER': 'tester'}

        offset = url_for("/contact/warandpeace")
        res = self.app.post(offset, extra_environ=extra_environ)

        print offset
        print res

        assert all(piece in res.body for piece in ['<form', '/contact/send/', '</form>']), 'Contact form not rendered'

    def test_contact(self):

        data = copy.deepcopy(TEST_DATADICT)
        data['private'] = False
        data['contact'][0]['email'] = 'kata.selenium@gmail.com'

        model.User(name="test_sysadmin", sysadmin=True).save()

        organisation = get_action('organization_create')({'user': 'test_sysadmin'}, {'name': 'test-organization',
                                                                                     'title': "Test organization"})
        data['owner_org'] = organisation.get('name')
        package = get_action('package_create')({'user': 'test_sysadmin'}, data)
        name = package['name']
        id = package['id']
        package_contact_id = utils.get_package_contacts(id)[0].get('id')

        send_contact_offset = url_for("/contact/send/{0}".format(id))
        res = self.app.post(send_contact_offset, params={'recipient': package_contact_id})
        assert res.status == 302

        dataset_offset = url_for("/dataset/{0}".format(name))
        res = self.app.post(dataset_offset)
        assert 'Message not sent' in res

        import base64
        import time

        cc = ContactController()
        _time = base64.b64encode(cc.crypto.encrypt(cc._pad(str(int(time.time())))))

        params = {
            'recipient': package_contact_id,
            'accept_logging': 'True'
        }

        self.app.post(send_contact_offset, params=params, status=302)
        res = self.app.post(dataset_offset)
        assert 'spam bot' in res

        _time = base64.b64encode(cc.crypto.encrypt(cc._pad(str(int(time.time())-21))))
        params = {
            'recipient': package_contact_id,
            'accept_logging': 'True'
        }
        self.app.post(send_contact_offset, params=params, status=302)
        offset = url_for("/dataset/{0}".format(name))
        res = self.app.post(offset)

        assert 'Message not sent' in res


class TestAuthorisation(KataWsgiTestCase):
    '''
    Test Kata authorisation functions
    '''

    @classmethod
    def teardown_class(cls):
        model.repo.rebuild_db()

    @classmethod
    def setup_class(cls):
        super(TestAuthorisation, cls).setup_class()
        model.repo.new_revision()
        model.Session.commit()

        users = [
            {'name': 'test_sysadmin',
             'sysadmin': True,
             'apikey': 'test_sysadmin',
             'password': 'test_sysadmin'},
            {'name': 'test_user',
             'sysadmin': False,
             'apikey': 'test_user',
             'password': 'test_user'},
            {'name': 'test_user2',
             'sysadmin': False,
             'apikey': 'test_user2',
             'password': 'test_user2'}
        ]
        CreateTestData.create_users(users)
        cls.test_user = user_model.User.get('test_user')
        cls.test_sysadmin = user_model.User.get('test_sysadmin')
        cls.api_test_sysadmin = ckanapi.TestAppCKAN(cls.app, apikey=cls.test_sysadmin.apikey)
        cls.api_test_user = ckanapi.TestAppCKAN(cls.app, apikey=cls.test_user.apikey)
        org_dict = {'name': 'test_organisation', 'title': 'Test Organisation'}
        cls.api_test_sysadmin.action.organization_create(**org_dict)
        cls.TEST_DATADICT = copy.deepcopy(TEST_DATADICT)
        cls.TEST_DATADICT['owner_org'] = 'test_organisation'

    def test_edit_not_available(self):
        '''
        Test that edit page is not available for random user
        '''
        TestAuthorisation.TEST_DATADICT['pids'][0]['id'] = 'primary_pid_1'
        package = TestAuthorisation.api_test_user.action.package_create(**TestAuthorisation.TEST_DATADICT)
        offset = url_for("/dataset/edit/{0}".format(package['name']))
        extra_environ = {'REMOTE_USER': 'russianfan'}
        res = self.app.get(offset, extra_environ=extra_environ, status=401)
        TestAuthorisation.api_test_user.call_action('package_delete', data_dict={'id': package['id']})


    def test_delete_not_available(self):
        '''
        Test that deletion of a dataset is not available
        for an unauthorised user
        '''
        package = TestAuthorisation.api_test_user.action.package_create(**TestAuthorisation.TEST_DATADICT)
        offset = url_for("/dataset/delete/{0}".format(package['name']))
        extra_environ = {'REMOTE_USER': 'russianfan'}

        res = self.app.get(offset, extra_environ=extra_environ)

        assert res.status == 200, 'Wrong status code (expecting 200)'  # Confirmation page
        res = res.forms[0].submit('delete')

        assert res.status == 302, 'Wrong status code (expecting 302)'  # Redirect to login page
        res = res.follow()

        assert res.status == 200, 'Wrong status code (expecting 200)'  # Login page
        assert 'Unauthorized to delete package' in res, \
            'The login page should alert the user about deleting being unauthorized'

        TestAuthorisation.api_test_user.call_action('package_delete', data_dict={'id': package['id']})

    def test_delete_authorized_own(self):
        """
            A non-admin should be able to delete its own created dataset.
        """
        org = copy.deepcopy(TEST_ORGANIZATION_COMMON)
        org['name'] = 'testdeleteauthorizedown'
        organization = get_action('organization_create')({'user': 'testsysadmin'}, org)

        data = copy.deepcopy(TEST_DATADICT)
        data['owner_org'] = organization['name']

        package = get_action('package_create')({'user': 'joeadmin'}, data)

        get_action('package_delete')({'user': 'joeadmin'}, {'id': package['id']})

        offset = url_for(controller='package', action='read', id=package['id'])
        res = self.app.get(offset)

        assert res.status == 200, 'The user should arrive to dataset page, since the package is deleted'


    def test_delete_authorized_external(self):
        """
            An editor should be able to delete a package from an external organization
        """

        # tester - organization editor (has a right to delete packages)
        org = copy.deepcopy(TEST_ORGANIZATION_COMMON)
        org['name'] = 'testdeleteauthorizedexternal'
        organization = get_action('organization_create')({'user': 'testsysadmin'}, org)

        # create a dataset under that organization
        data = copy.deepcopy(TEST_DATADICT)
        data['owner_org'] = organization['name']

        package = get_action('package_create')({'user': 'testsysadmin'}, data)

        # delete the package as 'tester'
        get_action('package_delete')({'user': 'tester'}, {'id': package['id']})

        # assert, that the package is not found
        offset = url_for(controller='package', action='read', id=package['id'])
        res = self.app.get(offset)

        assert res.status == 200, 'The user should arrive to dataset page, since the package is deleted'

    @raises(NotAuthorized)
    def test_delete_unauthorized_external(self):
        """
            A member should not be able to delete a package from an external organization
        """

        # joeadmin - organization member (does not have a right to delete packages)
        org = copy.deepcopy(TEST_ORGANIZATION_COMMON)
        org['name'] = 'testdeleteunauthorizedexternal'
        organization = get_action('organization_create')({'user': 'testsysadmin'}, org)

        # create a dataset under that organization
        data = copy.deepcopy(TEST_DATADICT)
        data['owner_org'] = organization['name']

        package = get_action('package_create')({'user': 'testsysadmin'}, data)

        # delete the package as 'tester'
        get_action('package_delete')({'user': 'joeadmin'}, {'id': package['id']})

        # The test should throw NotAuthorized exception

class TestURNExport(KataWsgiTestCase):
    '''
    Test urn export
    '''

    namespaces = {'u': 'urn:nbn:se:uu:ub:epc-schema:rs-location-mapping'}

    @classmethod
    def setup_class(cls):
        kata_model.setup()
        harvest_model.setup()

        model.User(name="test_sysadmin", sysadmin=True).save()

    @classmethod
    def teardown_class(cls):
        model.repo.rebuild_db()

    def test_urnexport(self):
        from ckanext.kata import controllers

        # Switch to use uncached urnexport:
        controllers.MetadataController.urnexport = controllers.MetadataController._urnexport

        offset = url_for('/urnexport')
        res = self.app.get(offset)

        # No datasets to export
        self.assertEquals(len(etree.fromstring(res.body).xpath("//u:identifier", namespaces=self.namespaces)), 0)
        assert res.body.count('<identifier>') == 0

        organization = get_action('organization_create')({'user': 'test_sysadmin'},
                                                         {'name': 'test-organization', 'title': "Test organization"})

        for i, (count, private, delete) in enumerate([(1, False, False), (1, True, False), (2, False, False),
                                                      (3, False, True), (4, False, False),
                                                      (6, False, False), (6, True, False), (8, False, False), (10, False, True), (12, False, False)]):
            data = copy.deepcopy(TEST_DATADICT)
            if i<=4:
                for pid in data.get('pids', []):
                    pid['id'] = pid.get('id') + unicode(i)
            elif i>4:
                for j, pid in enumerate(data.get('pids', [])):
                    if i%2 == 0:
                        pid['id'] = 'urn:nbn:fi:csc-ida1234' + unicode(j+i)
                    else:
                        pid['id'] = 'urn:nbn:fi:csc-kata1234' + unicode(j+i)

            # generate unique pids in a somewhat clumsy way...


            data['owner_org'] = organization['name']
            data['private'] = private

            package = get_action('package_create')({'user': 'test_sysadmin'}, data)

            if delete:
                get_action('package_delete')({'user': 'test_sysadmin'}, {'id': package['id']})

            res = self.app.get(offset)

            tree = etree.fromstring(res.body)
            self.assertEquals(len(tree.xpath("//u:identifier", namespaces=self.namespaces)), count)

            try:
                etree.XML(res.body)  # Validate that result is XML
            except etree.LxmlError:
                self.fail('Unexpected XML parsing error')


class TestKataApi(KataWsgiTestCase):
    '''
    Test custom HTTP API.
    '''

    def test_funder_autocomplete(self):
        result = self.app.get(
            url_for(controller="ckanext.kata.controllers:KATAApiController", action='funder_autocomplete',
                    incomplete=u'eu'))
        results = json.loads(unicode(result.body))['ResultSet']['Result']
        self.assertTrue({"Name": "EU muu rahoitus - EU other funding"} in results)


class TestMetadataSupplements(KataWsgiTestCase):
    '''
    Test metadata supplements.
    '''

    def test_01_button(self):
        '''
        Test that button renders
        '''
        organization = get_action('organization_create')({'user': 'testsysadmin'},
                                                         {'name': 'unseen-academy',
                                                          'title': "Unseen Academy"})

        data = copy.deepcopy(TEST_DATADICT)
        data['owner_org'] = organization['name']

        package = get_action('package_create')({'user': 'testsysadmin'}, data)
        offset = url_for(controller='package', action='read', id=package['id'])
        extra_environ = {'REMOTE_USER': 'testsysadmin'}
        res = self.app.get(offset, extra_environ=extra_environ)
        assert '/dataset/new_resource/' in res

    def test_02_formpage(self):
        '''
        Test that metadata supplement form renders
        '''
        organization = get_action('organization_create')({'user': 'testsysadmin'},
                                                         {'name': 'unseen-academy-1',
                                                          'title': "Unseen Academy 1"})

        data = copy.deepcopy(TEST_DATADICT)
        data['pids'][0]['id'] = u'unseen-primary-identifier'
        data['owner_org'] = organization['name']

        package = get_action('package_create')({'user': 'testsysadmin'}, data)

        package = get_action('package_show')({'user': 'testsysadmin'},
                                             {'id': package['id']})
        offset = url_for('/en/dataset/new_resource/{0}'.format(package['name']))
        extra_environ = {'REMOTE_USER': 'testsysadmin'}
        res = self.app.get(offset, extra_environ=extra_environ)
        assert 'resource-upload-field' in res

        get_action('package_delete')({'user': 'testsysadmin'}, package)
