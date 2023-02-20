from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseRedirect
import requests
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor

def getrequest(link):
   r = requests.get(
    url='Your Proxy Scrapeops Key',
    params={
      'api_key': 'YOUR API KEY',
      'url': link, 
    },
   )
   return r

def home(request):	
   mvname = request.POST.get('title')
   a = "https://www.imdb.com/find?q="+mvname+"&ref_=nv_sr_sm"
   imdb = "https://www.imdb.com"
   r = getrequest(a)
   soup = BeautifulSoup(r.content, 'html.parser')
   s = soup.find('div', class_='ipc-metadata-list-summary-item__tc').find('a')
   imdbid = s['href'].split('/')[2]
   i = "https://www.imdb.com"+s['href']
   j = getrequest(i)
   soup2 = BeautifulSoup(j.content, 'html.parser')
   links = soup2.find_all('a',class_="ipc-title-link-wrapper")
   newdata = {}
   for i in links:
     if("Photos" in i.text):
       newdata["photos"] = imdb+i['href']
     elif("Top cast" == i.text):
       cast = imdb+i['href']
     else:
       faqs = imdb+i['href']
   castpage = getrequest(cast)
   soup3 = BeautifulSoup(castpage.content, 'html.parser')
   production = soup3.find_all('table',class_="simpleTable simpleCreditsTable")
   gross = soup2.find_all('label',class_="ipc-metadata-list-item__list-content-item")
   data = getMovieDetails(imdbid)
   new = data['expanded']
   for i in gross:
      if(i.text[0] == '$'):
         newdata["Gross"] = i.text
   newdata["name"] = new[0]['name']
   newdata["image"] = new[0]['image']
   newdata["genre"] = new[0]['genre']
   try:
    newdata["keywords"] = new[0]['keywords'].split(',')
   except:
    newdata["keyword"] = ''
   try:
    newdata["date"] = new[0]['datePublished']
   except:
    newdata["date"] = ''
   try:
    newdata["duration"] = new[0]['duration'].split('PT')
   except:
    newdata["duration"] = ''
   newdata["rating"] = data['ratingValue']
   newdata["summary"] = data['summary_text']
   newdata["topcast"] = topcast(soup3)
   newdata["writing"] = writingcredits(production)
   newdata["direction"] = directioncredits(production)
   newdata["production"] = productioncredits(production)
   newdata["music"] = musiccredits(production)
   newdata["reviews"] = reviews(imdbid)

   return render(request,'home.html',{'newdata':newdata})

def movies(request):
	return render(request,'index.html') 

def getMovieDetails(imdbID):
   data = {}
   movie_url = "https://www.imdb.com/title/"+imdbID
   r = getrequest(movie_url)
   soup = BeautifulSoup(r.text, 'html.parser')
   jsonData = soup.find('script',{"type":"application/ld+json"})
   Moredata=[]
   jsonSourceObj=json.loads(jsonData.string)
   Moredata.append(jsonSourceObj)
   data["expanded"]=Moredata
   data["imdbID"] = imdbID
   title = soup.find('title')
   data["title"] = title.string
   data["Minutes"]=""
   try :
     data["Minutes"]=jsonSourceObj['duration']
   except :
     data["Minutes"]=""
   data["ratingValue"]=""
   try : 
      data["ratingValue"]= jsonSourceObj['aggregateRating']['ratingValue']
   except :
     data["ratingValue"]=""
     data["ratingCount"] =""
   try : 
      data["summary_text"]= jsonSourceObj['description']
   except :
     data["summary_text"]=""   
   try: 
     data['keywords']=jsonSourceObj['keywords']
   except :
      data['keywords']=""
   return data

def photosfun(link):
   imdb = "https://www.imdb.com"
   link2 = imdb+link['href']
   obj = getrequest(link2)
   soup = BeautifulSoup(obj.content, 'html.parser')
   try:
      di = soup.find('img',class_="sc-7c0a9e7c-0 hXPlvk")
   except:
      di = ""
   try:
      di = soup.find('img',class_="sc-7c0a9e7c-1 kJatiV")
   except:
      di = "" 
   if di != None:
     return di['src']
   else:
     return ""
def photos(request):
   photos = request.GET.get('photoslink')
   piclist = []
   photopage = getrequest(photos)
   photosoup = BeautifulSoup(photopage.content, 'html.parser')
   picdiv = photosoup.find('div',class_="media_index_thumb_list").find_all('a')
   with ThreadPoolExecutor(max_workers=10) as executor:
     for result in [executor.submit(photosfun, k) for k in picdiv]:
       res = result.result()
       if res != "":
         piclist.append(res)
   return render(request,'photos.html',{'piclist':piclist})


def reviews(ImdbId,sort="submissionDate",ratingFilter=10,dir="asc"):
  try :
    movie_url = "https://www.imdb.com/title/"+ImdbId+"/reviews/_ajax?"+"sort="+sort+"&dir="+dir+"&ratingFilter="+ratingFilter
    print(movie_url)
  except :
    movie_url = "https://www.imdb.com/title/"+ImdbId+"/reviews"+"/_ajax"
  r = getrequest(movie_url)
  soup = BeautifulSoup(r.text, 'html.parser')
  try :
    reviews = soup.find_all('div',{'class' : 'imdb-user-review'})
  except :
    pass
  reviews_text =[]
  for review in reviews :
    review_imdb={}
    try :
      review_imdb['reviewer_name']=review.find('span',{'class':'display-name-link'}).find('a').string.strip()
    except :
      review_imdb['reviewer_name']=""    
    try:
      short_review =review.find('a',{'class': 'title'})
      text=short_review.string.strip()
      review_imdb['short_review']=text
    except :
      review_imdb['short_review']=""
    
    reviews_text.append(review_imdb)    
  data=reviews_text
  return data


def topcast(soup3):
  cast = soup3.find('table',class_="cast_list")
  oddtr = cast.find_all('tr',class_='odd')
  eventr = cast.find_all('tr',class_='even')
  oddchar = []
  evenchar = []
  for i in oddtr:
      if(i.find('td',class_='character') != None):
          j = i.find('td',class_='character').find('a')
      if(j != None):
          oddchar.append(j.text)
      else:
          oddchar.append("None")           
  for i in eventr:
      if(i.find('td',class_='character') != None):
          j = i.find('td',class_='character').find('a')
      if(j != None):
          evenchar.append(j.text)
      else:
          evenchar.append("None")   
  bothchar = []
  for i in range(len(evenchar)):
      bothchar.append(oddchar[i])
      bothchar.append(evenchar[i])
  oddnames = []
  evennames = []
  bothnames = []
  for i in oddtr:
      l = i.find_all('a')
      if(l):
          oddnames.append(l[1].text.strip())
  for i in eventr:
      l = i.find_all('a')
      if(l):
          evennames.append(l[1].text.strip())
  for i in range(len(evennames)):
      bothnames.append(oddnames[i])
      bothnames.append(evennames[i])
  return dict(zip(bothnames,bothchar))


def writingcredits(production):
    wri1 = production[1].find_all('a')
    wri2 = production[1].find_all('td',class_="credit")
    l1 = [i.text.strip() for i in wri1]
    l2 = [i.text.strip() for i in wri2]
    return l1,l2
    
def directioncredits(production):
    dir1 = production[0].find_all('a')
    dir2 = production[0].find_all('td',class_="credit")
    l1 = [i.text.strip() for i in dir1]
    l2 = [i.text.strip() for i in dir2]
    return l1,l2
    
def productioncredits(production):
    pro1 = production[2].find_all('a')
    pro2 = production[2].find_all('td',class_="credit")
    l1 = [i.text.strip() for i in pro1]
    l2 = [i.text.strip() for i in pro2]
    return dict(zip(l1,l2))
    
def musiccredits(production):
    mus1 = production[3].find_all('a')
    mus2 = production[3].find_all('td',class_="credit")
    l1 = [i.text.strip() for i in mus1]
    l2 = [i.text.strip() for i in mus2]
    return l1,l2