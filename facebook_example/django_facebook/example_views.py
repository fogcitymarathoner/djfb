from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.views.decorators.csrf import csrf_protect
from django_facebook import facebook_required_lazy, facebook_required, \
    get_persistent_graph, require_persistent_graph
from django_facebook.utils import next_redirect


@facebook_required
def decorator_example(request, graph):
    '''
    Redirects the user to Facebook's oAuth dialog if the permissions
    requested in scope are not present

    default is FACEBOOK_DEFAULT_SCOPE
    '''
    if graph:
        # Proceed to load the users friends, or maybe post on their wall
        return HttpResponse('authorized')
    else:
        # this happens when the user denies the authentication request
        # or when there is a Facebook error
        return HttpResponse('user denied or error')


@facebook_required(scope=['publish_actions'])
def decorator_example_scope(request, graph):
    '''
    Same as above, but with a custom scope
    '''
    if graph:
        # Proceed to load the users friends, or maybe post on their wall
        return HttpResponse('authorized')
    else:
        # this happens when the user denies the authentication request
        # or when there is a Facebook error
        return HttpResponse('user denied or error')


@facebook_required_lazy
def lazy_decorator_example(request, graph):
    '''
    The lazy decorator is faster, but somewhat harder to use
    You have no guarantee that you have the required permissions
    The user will get redirected to the oAuth dialog if your facebook calls
    trigger a Facebook Exception
    '''
    if graph:
        # Proceed to load the users friends, or maybe post on their wall
        # any action triggering a facebook error will cause a redirect
        # to the facebook oAuth dialog
        if request.method == 'POST':
            # requesting friends will fail if we don't have permissions
            # the exception will trigger a redirect to the oAuth dialog
            friends = graph.get('me/friends')

        return HttpResponse('authorized')
    else:
        # this happens when the user denies the authentication request
        return HttpResponse('user denied or error')


@facebook_required(scope='publish_stream')
@csrf_protect
def wall_post(request):
    print 'example view wall post'
    print request.GET
    print request.POST
    print 'message %s'%request.POST.get('message')
    fb = get_persistent_graph(request)
    print fb
    message = request.GET.get('message')
    if message:
        fb.set('me/feed', message=message)
        messages.info(request, 'Posted the message to your wall')
        return next_redirect(request)


@facebook_required(scope='publish_stream,user_photos')
@csrf_protect
def image_upload(request):
    fb = get_persistent_graph(request)
    pictures = request.POST.getlist('pictures')

    if pictures:
        for picture in pictures:
            fb.set('me/photos', url=picture, message='the writing is one The '
                   'wall image %s' % picture)

        messages.info(request, 'The images have been added to your profile!')

        return next_redirect(request)


@facebook_required_lazy(canvas=True)
def canvas(request):
    '''
    Example of a canvas page.
    Canvas pages require redirects to work using javascript instead of http headers
    The facebook required and facebook required lazy decorator abstract this away
    '''
    context = RequestContext(request)
    fb = require_persistent_graph(request)
    likes = fb.get('me/likes')['data']
    context['likes'] = likes

    return render_to_response('django_facebook/canvas.html', context)


@facebook_required(scope='publish_actions')
@csrf_protect
def open_graph_beta(request):
    '''
    Simple example on how to do open graph postings
    '''
    message = request.POST.get('message')
    if message:
        fb = get_persistent_graph(request)
        entity_url = 'http://www.fashiolista.com/item/2081202/'
        fb.set('me/fashiolista:love', item=entity_url, message=message)
        messages.info(request,
                      'Frictionless sharing to open graph beta action '
                      'fashiolista:love with item_url %s, this url contains '
                      'open graph data which Facebook scrapes' % entity_url)


@facebook_required(scope='publish_actions')
@csrf_protect
def remove_og_share(request):
    from django_facebook.models import OpenGraphShare
    graph = get_persistent_graph(request)
    og_share_id = request.POST.get('og_share_id')
    if og_share_id:
        shares = OpenGraphShare.objects.filter(id=og_share_id)
        for share in shares:
            share.remove(graph)
