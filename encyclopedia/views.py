from django.shortcuts import render
from django.http import HttpResponse
from django import forms

from markdown2 import Markdown

from . import util

# Variable for performing the required markdown (converting HTML into user friendly language)
markdowner = Markdown()

# Set up Django forms for our search function
class Search(forms.Form):
    result = forms.CharField(label="Search Results")

# Default page for listing the articles currently in the encyclopedia
def index(request):
    # Attempting to implement the search functionality
    # If the request method is post (i.e. the search box is submitted)
    if request.method == "POST":
        # Call the Django Search class
        search = Search(request.POST)
        # Create a list for any partial matches
        partial_results = []
        # Create a list of all of the current entries
        current_entries = util.list_entries()
        # If the search input is valid
        if search.is_valid():
            # Clean the data and store in a result variable
            result = search.cleaned_data["search"]
            # Loop through the list of entries
            for i in current_entries:
                # If the result matches one of the entries
                if result.lower() == current_entries[i].lower():
                    # Return that result (same as going to the page directly)
                    return render(request, "encyclopedia/article.html", {
                        "article": markdowner.convert(util.get_entry(result)),
                        "title": result,
                        "search": search
                    })
                # If the result partially matches one of the entries
                if result.lower() in current_entries[i].lower():
                    # Update the partial results list
                    partial_results.append(i)
            # If no result has been found, then render and return the search results list
            return render(request, "encyclopedia/search.html", {
                "result": result,
                "partial_results": partial_results,
                "search": Search()
            })
    # Else if request method is not POST, then bring up the index page
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries(),
        "search": Search()
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

def search(request, title):
