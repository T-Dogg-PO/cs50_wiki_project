from django.shortcuts import render
from django.http import HttpResponse
from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from markdown2 import Markdown

from . import util

# Variable for performing the required markdown (converting HTML into user friendly language)
markdowner = Markdown()

# Set up a Django form for our search function
class Search(forms.Form):
    result = forms.CharField()

# Set up a Django form for adding a new page
class New(forms.Form):
    title = forms.CharField(label="Title", required=True, widget=forms.Textarea)
    body = forms.CharField(label="Body", required=True, widget=forms.Textarea)

    # Function to validate that the new article being created does not have a duplicate title. Not currently working.
    # Could not get the error message from this code snippet to show before the new form loaded. Will come back to this
    # in the future. For now the error message is handled in the new article function itself
    def clean_title(self):
        title = self.cleaned_data['title']
        current_entries = util.list_entries()

        for current_title in current_entries:
            if title.lower() == current_title.lower():
                raise ValidationError(_(mark_safe("An article with this title already exists here. Please change the "
                                                  "title of your article and resubmit or edit the existing article.")))

        return title


# Default page for listing the articles currently in the encyclopedia
def index(request):
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries(),
    })

# Page for when you go to a specific url with an article. Context is the title of the page passed in
def article(request, title):
    # Check to see if article exists in the database. If not return error
    if not util.get_entry(title):
        return HttpResponse("404 - article not found in database")
    # Render the articles html page, converting the markdown language on the way
    return render(request, "encyclopedia/article.html", {
        "article": markdowner.convert(util.get_entry(title)),
        "title": title
    })

# Page that the user is directed to when using the search box
def search(request):
    # Check that the request method is POST (i.e. the user is submitting the form)
    if request.method == "POST":

        # Take in the data the user submitted and save it in search_data
        search_data = Search(request.POST)

        # Check that the submitted data is valid
        if search_data.is_valid():

            # Isolate the input that the user has provided
            result = search_data.cleaned_data["result"]

            # Get a list of the entries that we currently have in our wiki
            current_entries = util.list_entries()

            # Create a list for partial matching results
            partial_results = []

            # Loop through the current entries, checking if the search term (in 'result') is contained in each of the
            # current titles. If yes, add to partial_results
            for filename in current_entries:
                if result.lower() in filename.lower():
                    partial_results.append(filename)

            # 'Pythonic' way of writing the above loop
            # partial_results = [filename for filename in current_entries if result.lower() in filename.lower()]

            # Check to see if anything exists in partial_results. If no, render the search.html page and
            # display "No results found"
            if len(partial_results) == 0:
                return render(request, "encyclopedia/search.html", {
                    "search_data": search_data,
                    "error": "No results found",
                    "no_results": True
                })

            # Else, check that both partial_results contains one result and this result matches the search term.
            # If yes, display the article in question
            elif len(partial_results) == 1 and partial_results[0].lower() == result.lower():
                title = partial_results[0]
                return article(request, title)

            # Else, show the list of partially matching results with links to those articles
            else:
                # Check the list of partial_results to see if there is an exact match for the search result in the list.
                # If yes, display the article in question

                for filename in partial_results:
                    if result.lower() == filename.lower():
                        return article(request, filename)

                # Otherwise if there is no exact matches, display the search.html page, passing in the partial_results
                return render(request, "encyclopedia/search.html", {
                    "partial_results": partial_results,
                    "search_data": search_data
                })

        else:
            return index(request)

    return index(request)

# Page that user can use to create new articles
def new(request):
    # Check to see if the user is going to the New Article page, or if they are submitting information from this page
    # If the method is post (i.e. they are saving their new article) then save and publish the article
    args = {}
    if request.method == "POST":
        # Store the information from the New form in new_article
        new_article = New(request.POST)

        # Check submitted article is valid
        if new_article.is_valid():
            # Isolate the article title and body
            title = new_article.cleaned_data["title"]
            body = new_article.cleaned_data["body"]

            # Create the new entry and redirect to the new entries page
            util.save_entry(title, body)
            return article(request, title)

        # If it's not valid (i.e. the article title already exists) then stay on this page. TO DO - get information
        # to stay on the page instead of losing it on unsuccessful submission
        else:
            return render(request, "encyclopedia/new.html", {
                "errors": True,
                "error_message": "An article with this title already exists here. Please change the title of your "
                                 "article and resubmit or edit the existing article.",
                "new": New()
            })

    # Else load the new article page
    else:
        return render(request, "encyclopedia/new.html", {
            "new": New()
        })