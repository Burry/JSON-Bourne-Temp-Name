#!/usr/bin/python3

from __future__ import print_function
from random import *
import hashlib
import requests
import time
import sys
from selenium import webdriver #type sudo easy-install selenium (mac)
#from selenium.webdriver.support.ui import Select
import nltk, json
import ScrapeFetchedRecipes
import re
from bs4 import BeautifulSoup
# nltk.download('punkt')
# nltk.download('maxent_treebank_pos_tagger')
# nltk.download('averaged_perceptron_tagger')

class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def writelines(self, datas):
       self.stream.writelines(datas)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)

sys.stdout = Unbuffered(sys.stdout)
#this function is called for each recipe that is scraped.
#The input is a list of all the ingredients in the recipe, an output is a printed JSON object
#containing nutritional data for every ingredient, and nutritional value for the recipe
#in addition to all the other information about the recipe.
def getNVforRecipe(ingredient_list):
    searchFlag = 0
    quantityFlag = 0
    errors = []#this list contains ingredients that are insignificant, or just dont provide enough information,
    #or provide too much information.
    IngredientIDList = []
    filter_results = [] #list containing output ingredient
    totalNVstat = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]#This list sums the nutritional value of every ingredient in a recipe. each entry in this list corresponds to a field of nutritional value e.g. Carbs or Total Fat.
    k = 0 #ingredient list index
    #loop through each ingredient in ingredient list from ScrapeFetchedRecipes.py file

    while k < len(ingredient_list):
        searchFlag = 0
        #remove white space padding, periods, and make all lowercase
        input_ingredient = ingredient_list[k].strip() #grab an ingredient string from list
        input_ingredient = input_ingredient.lower()#convert to all lowercase
        input_ingredient = input_ingredient.replace('.','').replace(' cold, ', ' ')#remove "." and "cold"
        #used to address "4 to 6 cups...". Selects the larger quantity
        if re.match(r'[1-9] to [1-9]', input_ingredient):
            #selects the string on the right side of " to " e.g. 6 cups
            input_ingredient = input_ingredient.split(' to ', 1)[1]
            input_ingredient.strip() #remove extra white space. this is probobly unnecessary
        if ',' in input_ingredient:
            #take the string to the right of the comma
            input_ingredient = input_ingredient.split(',',1)[0]
        if ' or ' in input_ingredient:#the following will select the first option in an ambiguity case.
            right = input_ingredient.split(' or ', 1)[1]
            left = input_ingredient.split(' or ', 1)[0]
            #print 'right is: ' + right
            if ' ' in right:
                right = right.split(' ', 1)[1]#remove the first word in the string to the right of " or "
                input_ingredient = left + ' ' + right
            else:
                #this means that there was only one word following the "or". this means that it was at
                #the end of the sentance. Most likely dont want something to the right of the "or" if its
                #at the end of the sentance.
                input_ingredient = left
            #print 'resulting string of extracted \'or\': ' + input_ingredient

        #check to see if a quantity is specified
        quantity_specified = re.match(r'[1-9/]{1,3}|one|two|three|four|five|six', input_ingredient)
        #a few words signify insignificance, or should never be in an ingredient name.
        if 'recipe' in input_ingredient or 'black pepper' in input_ingredient or ' salt' in input_ingredient or ' spray ' in input_ingredient or ':' in input_ingredient:
            errors.append(input_ingredient)
            input_ingredient = input_ingredient + ' (salt/pepper/spray/recipe/:)'
            filter_results.append(input_ingredient)
            k+=1 #increment the ingredient list index and skip to the next loop iteration
            continue
        if quantity_specified:
            if 'parmesan' in input_ingredient:
                ingredient = 'parmesan cheese'
                #print ingredient
                #k += 1

            elif 'garlic' in input_ingredient and 'powder' not in input_ingredient:
                ingredient = 'garlic'
                #print ingredient
                #k += 1

            elif 'cucumber' in input_ingredient:
                ingredient = 'cucumber'
                #print ingredient
                #k += 1
            elif 'unsalted butter' in input_ingredient:
                ingredient = 'unsalted butter'

            else:
                Words = input_ingredient.split() #split raw ingredient string into a list of words
                ingredient = ' '#initialize output string
                for word in Words:#loop through each word of input_ingredient
                    if re.match(r'[0-9]+-', word) or re.match(r'[1-9]/[1-9]-', word): #skip over quantity specifier
                        continue
                    #tag each word with its part of speech
                    tokenized_word = nltk.word_tokenize(word)
                    POS =  nltk.pos_tag(tokenized_word)

                    #construct the output string by appending all noun and adjective words
                    if POS[0][1] == 'NN' or POS[0][1] == 'NNS' or POS[0][1] == 'JJ':
                        ingredient = ingredient + POS[0][0] + ' '
                ingredient = ingredient.lower() #ensure everything is in lowercase
                #remove the unwanted adjectives/nouns
                ingredient = ingredient.replace(' miniature ', ' ').replace(' beaten ', ' ').replace(' bags ', ' ').replace(' bag ', '').replace(' teaspoons ', ' ').replace(' teaspoon ', ' ').replace(' cups ', ' ').replace(' cup ', ' ').replace(' container ', ' ').replace(' tablespoons ', ' ').replace(' tablespoon ', ' ').replace(' box ', ' ').replace(' ounces ', ' ').replace(' packages ', ' ').replace(' package ', ' ').replace(' packets', ' ').replace(' pounds ', ' ')
                ingredient = ingredient.replace(' pound ','').replace(' pints ', ' ').replace(' cans ', ' ').replace(' can ', ' ').replace(' pint ', ' ').replace(' pure ', ' ').replace(' jar ', ' ').replace(' tsp ', ' ').replace(' tbsp ', ' ').replace(' large ', ' ').replace(' small ', ' ').replace(' medium ', ' ').replace(' dairy ', ' ').replace(' aisle ', ' ').replace(' chopped ', ' ').replace(' optional ', ' ').replace(' packed ', ' ').replace(' leftover ', ' ')
                ingredient = ingredient.replace(' delicious ', ' ').replace(' cooked ', ' ').replace(' cook ', ' ').replace(' note ', ' ').replace(' water ', ' ').replace(' store-bought ', ' ').replace(' good ', ' ').replace(' sprigs ', ' ').replace(' inches ', ' ').replace(' chunks ', ' ').replace(' head ', ' ').replace(' stalks ', ' ').replace(' extra ', ' ').replace(' ice cold ', ' ').replace(' stick ', ' ').replace(' homemade ', ' ').replace(' dry ', ' ')

                ingredient = ingredient.replace(' pieces ', ' ').replace(' cut ', ' ')
                #special cases
                if 'goya' in ingredient:
                    ingredient = '16 bean soup mix'
                elif 'red pepper flakes' in ingredient:
                    ingredient = 'crushed red pepper'

                #ensure that the only time there is a '-' is between whole number and fraction in quantity
                #this combines the quantity into one word.
                input_ingredient = input_ingredient.replace('-', ' ')
                m = re.match(r'[1-9] [1-9]/[1-9]', input_ingredient)
                if m:
                    Num, space, rest = input_ingredient.partition(' ')
                    input_ingredient = Num + '-' + rest
                #grab the '1 cup' or '1 pound' part of ingredient, store as string called quantity
                array = input_ingredient.split()
                quantity = array[0] + ' ' + array[1] #quantity assumed to be first two words
        else:#no quantity specified, add to error list, skip to next ingredient
            k+=1
            errors.append(input_ingredient)
            input_ingredient = input_ingredient + ' (no quantity specified)'
            filter_results.append(input_ingredient)
            continue
        filter_results.append(ingredient)#add re-formatted ingredient to list for debugging
############        BEGIN SEARCH        ##############
        link_to_data = search(ingredient)#call search function
        #if no search results
        if (link_to_data == ' '):
            searchFlag = 1
            ingredient = ingredient.replace('dinner','')
            g = len(ingredient.split())
            if g >= 3:
                split = ingredient.rsplit(' ', 3)#split from the right, remove second to last word
                ingredient = split[1] + ' ' + split[2]
                filter_results.append(ingredient)
            elif g <= 2:
                ingredient = ingredient.rsplit(' ', 2)[1]
                filter_results.append(ingredient)
            link_to_data = search(ingredient)
############# BEGIN SCRAPE #################
        #if still no search results
        if(link_to_data == ' '):
            #print 'ingredient not found'
            errors.append(ingredient)
            filter_results.append('No link found.')
        #if search results, get all nutritional value
        else:
            filter_results.append(link_to_data)
            factor = 0
            ingredient_qty = 0
            IngredientNVdataG = []
            calories = ' '
            fatCal = ' '
            totalFat = ' '
            satFat = ' '
            cholesterol = ' '
            sodium = ' '
            sugar = ' '
            protein = ' '
            fiber = ' '
            totalCarbs = ' '
            calcium = ' '
            units = ' '
            r = requests.get(link_to_data)
            content = r.content
            soup = BeautifulSoup(content, 'html.parser')
            #grab calories per unit of food
            cal_div = soup.find('span', {'id' : 'mCal' })
            if cal_div:
                calories = cal_div.get_text()
                IngredientNVdataG.append(calories)
            #grab units of food
            units_select = soup.find('select', {'id' : 'units'})
            if units_select:
                units_option = units_select.find('option', {'value' : '0'})
                if units_option:
                    units = units_option.get_text()
            #if calories != ' ':
                #print 'There are ' + calories + ' calories in 1 ' + units
            #grab calories from fat
            fatCal_tr = soup.find('tr' , {'class' : 'fat-calories'})
            if fatCal_tr:
                fatCal_span = fatCal_tr.find('span', {'class' :'amount'})
                if fatCal_span:
                    fatCal = fatCal_span.get_text()
                    IngredientNVdataG.append(fatCal)
            #if fatCal != ' ':
                #print 'There are ' + fatCal + ' calories from fat in 1 ' + units
            #grab total fat
            totalFat_tr = soup.find('tr' , {'class' : 'total-fat'})
            if totalFat_tr:
                totalFat_td = totalFat_tr.find('td', {'class' :'amount'})
                if totalFat_td :
                    totalFat = totalFat_td.get_text()
                    IngredientNVdataG.append(totalFat)
            #if totalFat != ' ':
                #print 'There are ' + totalFat + ' of fat in 1 ' + units
            #grab saturated fat
            satFat_tr = soup.find('tr' , {'class' : 'sat-fat'})
            if satFat_tr:
                satFat_td = satFat_tr.find('td', {'class' :'amount'})
                if satFat_td :
                    satFat = satFat_td.get_text()
                    IngredientNVdataG.append(satFat)
            #if satFat != ' ':
                #print 'There are ' + satFat + ' of saturated fat in 1 ' + units
            #grab Cholesterol
            cholesterol_tr = soup.find('tr' , {'class' : 'cholesterol'})
            if cholesterol_tr:
                cholesterol_td = cholesterol_tr.find('td', {'class' :'amount'})
                if cholesterol_td :
                    cholesterol = cholesterol_td.get_text()
                    IngredientNVdataG.append(cholesterol)
            #if cholesterol != ' ':
                #print 'There are ' + cholesterol + ' of cholesterol in 1 ' + units
            #grab Sodium
            sodium_tr = soup.find('tr' , {'class' : 'sodium'})
            if sodium_tr:
                sodium_td = sodium_tr.find('td', {'class' :'amount'})
                if sodium_td :
                    sodium = sodium_td.get_text()
                    IngredientNVdataG.append(sodium)
            #if sodium != ' ':
                #print 'There are ' + sodium + ' of sodium in 1 ' + units
            #grab Total Carbs
            totalCarbs_tr = soup.find('tr' , {'class' : 'total-carbs'})
            if totalCarbs_tr:
                totalCarbs_td = totalCarbs_tr.find('td', {'class' :'amount'})
                if totalCarbs_td :
                    totalCarbs = totalCarbs_td.get_text()
                    IngredientNVdataG.append(totalCarbs)
            #if totalCarbs != ' ':
                #print 'There are ' + totalCarbs + ' total carbs in 1 ' + units
            #grab fiber
            fiber_tr = soup.find('tr' , {'class' : 'fiber'})
            if fiber_tr:
                fiber_td = fiber_tr.find('td', {'class' :'amount'})
                if fiber_td :
                    fiber = fiber_td.get_text()
                    IngredientNVdataG.append(fiber)
            #if fiber != ' ':
                #print 'There are ' + fiber + ' of fiber in 1 ' + units
            #grab sugar
            sugar_tr = soup.find('tr' , {'class' : 'sugars'})
            if sugar_tr:
                sugar_td = sugar_tr.find('td', {'class' :'amount'})
                if sugar_td :
                    sugar = sugar_td.get_text()
                    IngredientNVdataG.append(sugar)
            #if sugar != ' ':
                #print 'There are ' + sugar + ' of sugar in 1 ' + units
            #grab protein
            protein_tr = soup.find('tr' , {'class' : 'protein'})
            if protein_tr:
                protein_td = protein_tr.find('td', {'class' :'amount'})
                if protein_td :
                    protein = protein_td.get_text()
                    IngredientNVdataG.append(protein)
            #if protein != ' ':
                #print 'There are ' + protein + ' of protein in 1 ' + units
            #grab calcium
            calcium_tr = soup.find('tr' , {'class' : 'calcium'})
            if calcium_tr:
                calcium_td = calcium_tr.find('td', {'class' :'amount'})
                if calcium_td :
                    calcium = calcium_td.get_text()
                    IngredientNVdataG.append(calcium)
############CREATE JSON OBJECT FROM DATA############################
            ingredient_data = {}
            nutrition_data = {}

            #remove mg and < from scraped nutritonal data, and add it to a dictionary object
            nutrition_data['calTotal'] = calories.replace('m','').replace('g','').replace('<', '')
            nutrition_data['calFromFat'] = fatCal.replace('m','').replace('g','').replace('<', '')
            nutrition_data['totalFat'] = totalFat.replace('m','').replace('g','').replace('<', '')
            nutrition_data['saturatedFat'] = satFat.replace('m','').replace('g','').replace('<', '')
            nutrition_data['cholesterol'] = cholesterol.replace('m','').replace('g','').replace('<', '')
            nutrition_data['sodium'] = sodium.replace('m','').replace('g','').replace('<', '')
            nutrition_data['carbs'] = totalCarbs.replace('m','').replace('g','').replace('<', '')
            nutrition_data['fiber'] = fiber.replace('m','').replace('g','').replace('<', '')
            nutrition_data['sugar'] = sugar.replace('m','').replace('g','').replace('<', '')
            nutrition_data['protein'] = protein.replace('m','').replace('g','').replace('<', '')
            nutrition_data['calcium'] = calcium.replace('m','').replace('g','').replace('<', '')

            # if searchFlag == 1:
            #     ingredient_data['name'] = ingredient_list[k].strip() + '*ingredient search result warning'
            # elif quantityFlag = 1:
            #     ingredient_data['name'] = ingredient_list[k].strip() + '*nutritional value result warning (due to )'
            # else:
            #     ingredient_data['name'] = ingredient_list[k].strip()

            ingredient_data['type'] = 'ingredient'

            ingredient_id = str(hashlib.md5(ingredient + str(random())).hexdigest())[:24]
            ingredient_data['_id'] = ingredient_id
            ingredient_data['nutrition'] = nutrition_data
            IngredientIDList.append(ingredient_id)

            # if searchFlag == 1:
            #     ingredient_data['name'] = ingredient_list[k].strip() + '*ingredient search result warning'
            # elif quantityFlag = 1:
            #     ingredient_data['name'] = ingredient_list[k].strip() + '*nutritional value result warning (due to )'
            # else:
            #     ingredient_data['name'] = ingredient_list[k].strip()
            # ingredientJSON = json.dumps(ingredient_data)
            # if ingredient_id not in ScrapeFetchedRecipes.all_unique_ingredientID:
            #     ScrapeFetchedRecipes.all_unique_ingredientID.append(ingredient_id)
            #     print (ingredientJSON)
################# BEGIN CALCULATING NUTRITIONAL VALUE OF ENTIRE RECIPE #######################
            g = len(units)-1
            if g > 0 and ')' == units[g] and 'oz' in units:#only preform calculation if NV data specifies oz for its unit in parenthesis at the end
                units = units.rsplit('(',2)[1] #get rid of parenthesis
                units = units.replace(')', '')
                units = units.split()[0]#get rid of letters
                NVunitOZ = float(units)#convert to float
                #print NVunitOZ #number of ounces that give fetched NV statistics (in float form)
                q = array[0] #quantity specified in ingredient, as a string
                #print input_ingredient

                #print 'units in DB are:', units
                #print quantity #string specifying amount of ingredient and unit
                #extract amount and convert to floating point
                if '-' not in q and '/' not in q: #if q is a whole number
                    if q == 'one':
                        q = 1.0
                    elif q == 'two':
                        q = 2.0
                    elif q == 'three':
                        q = 3.0
                    elif q == 'four':
                        q = 4.0
                    elif q == 'five':
                        q = 5.0
                    elif q == 'six':
                        q = 6.0
                    else:
                        ingredient_qty = float(q)
                else:
                    if '-' in q and '/' in q: #if q is a whole number plus a fraction
                        whole = q.rsplit('-')[0]
                        a = q.split('-')[1]
                    elif '/' in q: #if q is just a fraction
                        a = q
                    numerator = a.split('/')[0]
                    denominator = a.split('/')[1]
                    n = float(numerator)
                    d = float(denominator)
                    r = n/d #float version of fraction

                    ingredient_qty = float(r)
                    if '-' in q:
                        ingredient_qty = ingredient_qty + float(whole)

                #naming convention sucks here
                if re.match(r'.*\([1-9]',input_ingredient):#figure out pattern here
                    unit_extract = input_ingredient.split('(', 1)[1]
                    unit_extract = unit_extract.split(')',1)[0]
                    #print unit_extract
                    q_extract = unit_extract.split()[0]
                    #print q_extract
                    ingredient_qty = ingredient_qty * float(q_extract)
                    quantity = unit_extract.split()[1]
                    #print quantity
                    #print input_ingredient
                #unit conversion on ingredient side
                if 'teaspoon' in  quantity:
                    ingredient_qtyOZ = ingredient_qty*0.16667
                elif 'tablespoon' in quantity:
                    ingredient_qtyOZ = ingredient_qty*0.5
                elif 'cup' in quantity:
                    ingredient_qtyOZ = ingredient_qty*8
                elif 'gallon' in quantity:
                    ingredient_qtyOZ = ingredient_qty*128
                elif 'quart' in quantity:
                    ingredient_qtyOZ = ingredient_qty*32
                elif 'pint' in quantity or 'pound' in quantity:
                    ingredient_qtyOZ = ingredient_qty*16

                elif 'ounce' in quantity or 'oz' in quantity:
                    ingredient_qtyOZ = ingredient_qty
                elif True:
                    if 'onion' in ingredient:
                        NVunitOZ = 1.0
                        ingredient_qtyOZ = SelectUnits(link_to_data, 'whole \[6')
                        #print 'Called dropdown function on: ' + ingredient + 'with key of: ' + array[1] + ' which returned factor of: ', ingredient_qtyOZ
                    elif 'celery' in ingredient:
                        NVunitOZ = 1.0
                        ingredient_qtyOZ = SelectUnits(link_to_data, 'stalk, 12')
                        #print 'Called dropdown function on: ' + ingredient + 'with key of: ' + array[1] + ' which returned factor of: ', ingredient_qtyOZ
                    else:
                        NVunitOZ = 1.0
                        ingredient_qtyOZ = SelectUnits(link_to_data, 'large')
                        #print 'Called dropdown function on: ' + ingredient + 'with key of: ' + array[1] + ' which returned factor of: ', ingredient_qtyOZ
                # else:
                #     #print 'bad unit is: ' + quantity + ' for ingredient: ' + ingredient
                #     errors.append(input_ingredient)
                #     input_ingredient = input_ingredient + ' (bad units)'
                #     filter_results.append(input_ingredient)
                #     #filter_results.append('Bad unit specifier')
                #     ingredient_qtyOZ = 0.0
                #     # NVunitOZ = 1

                factor = ingredient_qtyOZ/NVunitOZ #multiply fetched NV data by this constant to get NV of ingredient
                if factor == 1.0:
                    quantityFlag = 1
            #sum it all up
                i = 0
                #j = len(IngredientNVdataG)
                while i < len(IngredientNVdataG):
                    IngredientNVdataG[i] = IngredientNVdataG[i].replace('g','').replace('m', '').replace('<' , '')
                    IngredientNVdataG[i] = float(IngredientNVdataG[i])
                    totalNVstat[i] = (factor * IngredientNVdataG[i]) + totalNVstat[i]
                    i += 1
            if searchFlag == 1:
                ingredient_data['name'] = ingredient_list[k].strip() #+ '*ingredient search result warning'
            elif quantityFlag == 1:
                ingredient_data['name'] = ingredient_list[k].strip() #+ '*nutritional value result warning'
            else:
                ingredient_data['name'] = ingredient_list[k].strip()
            ingredientJSON = json.dumps(ingredient_data)
            if ingredient_id not in ScrapeFetchedRecipes.all_unique_ingredientID:
                ScrapeFetchedRecipes.all_unique_ingredientID.append(ingredient_id)
                print (ingredientJSON)
        k += 1
    #display data
    # print 'For ' + ScrapeFetchedRecipes.Amount.strip() + ':'
    # print 'There are ' , totalNVstat[0] , ' calories in this recipe'
    # print 'There are ' , totalNVstat[1] , ' calories from fat in this recipe'
    # print 'There are ' , totalNVstat[2] , 'g of fat in this recipe'
    # print 'There are ' , totalNVstat[3] , 'g of saturated fat in this recipe'
    # print 'There are ' , totalNVstat[4] , 'mg of cholesterol in this recipe'
    # print 'There are ' , totalNVstat[5] , 'mg of sodium in this recipe'
    # print 'There are ' , totalNVstat[6] , 'g total carbs in this recipe'
    # print 'There are ' , totalNVstat[7] , 'g of fiber in this recipe'
    # print 'There are ' , totalNVstat[8] , 'g of sugar in this recipe'
    # print 'There are ' , totalNVstat[9] , 'g of protein in this recipe'
    # print 'There are ' , totalNVstat[10] , 'mg of calcium in this recipe'

    recipe_nutrition_data = {}
    recipe_nutrition_data['calTotal'] = totalNVstat[0]
    recipe_nutrition_data['calFromFat'] = totalNVstat[1]
    recipe_nutrition_data['totalFat'] = totalNVstat[2]
    recipe_nutrition_data['saturatedFat'] = totalNVstat[3]
    recipe_nutrition_data['cholesterol'] = totalNVstat[4]
    recipe_nutrition_data['sodium'] = totalNVstat[5]
    recipe_nutrition_data['carbs'] = totalNVstat[6]
    recipe_nutrition_data['fiber'] = totalNVstat[7]
    recipe_nutrition_data['sugar'] = totalNVstat[8]
    recipe_nutrition_data['protein'] = totalNVstat[9]
    recipe_nutrition_data['calcium'] = totalNVstat[10]

    recipe_data = {}
    time = ScrapeFetchedRecipes.Cook_Time
    #print time
    if time != '':
        if 'hr' in time:
            hours = float(time.split('hr')[0])
            if 'min' in time:
                minutes = time.split('hr')[1]
                minutes = float(minutes.split('min')[0])
                time = hours*60 + minutes
            else:
                time = hours*60
        else:
            time = float(time.replace(' min', ''))
    recipe_data['name'] = ScrapeFetchedRecipes.title
    recipe_data['type'] = 'recipe'
    recipe_data['origURL'] = ScrapeFetchedRecipes.r.url
    recipe_data['steps'] = ScrapeFetchedRecipes.dirList
    recipe_data['time'] = time
    recipe_data['servings'] = ScrapeFetchedRecipes.Amount.strip()
    recipe_data['ingredients'] = IngredientIDList
    recipe_data['nutrition'] = recipe_nutrition_data
    recipe_data ['author']= ScrapeFetchedRecipes.author
    recipe_data['photoURL'] = ScrapeFetchedRecipes.image_src
    json_data = json.dumps(recipe_data)
    #print 'start response'
    print(json_data)

    file = open('ingredient_name.txt', 'a')
    for item in filter_results:
        item = item.encode('utf-8')
        file.write("%s\n" % item)
    file.close()
    file = open('noSearchResults.txt', 'a')
    for item in errors:
        item = item.encode('utf-8')
        file.write("%s\n" % item)
    file.close()
    return
def SelectUnits(link, key):
    driver = webdriver.Chrome(sys.argv[2])#this path is the path to chromedriver, downloadale from https://chromedriver.storage.googleapis.com/index.html?path=2.33/
    driver.get(link)
    time.sleep(2)
    calories_div = driver.find_element_by_id('mCal')
    caloriesOld = calories_div.text
    #print calories
    form = driver.find_element_by_id('units')
    for option in form.find_elements_by_tag_name('option'):
        if re.match(key, option.text):
            option.click()
            time.sleep(2)
            break
    calories_div = driver.find_element_by_id('mCal')
    caloriesNew = calories_div.text
    n = float(caloriesNew)
    d = float(caloriesOld)

    factor = n/d
    driver.quit()
    return factor
def search(ingredient):
    keywords = ingredient.split() #split ingredients into array of keywords
    search = ingredient.replace(' ', '+')#this used to construct a link to search results (search uses GET requests)

    #construct link to search results
    part1 = 'http://www.calorieking.com/foods/search.php?keywords='
    part2 = '&go.x=0&go.y=0&go=Go'
    url = part1 + search + part2

    #grab HTML for page of search results
    r = requests.get(url)
    content = r.content
    soup = BeautifulSoup(content, 'html.parser')
    #initialize empty string (used to check for no results case)
    link_to_data = ' '
    #filter through links on search results page to find best result
    #most intellegent search, checks if category of link contains keywords
    for category in soup.find_all('div', {'class' : 'food-search-result left-vertical-border-green'}):
        subCategorySpan = category.find('span' , {'class' : 'food-search-category'} )
        subCategory = subCategorySpan.get_text()
        # print keywords[len(keywords) - 1]
        # print subCategory.lower()
        i = len(keywords) - 1

        if i == 0 and keywords[i] in subCategory.lower():
            #print 'yes!'
            optimizedLink = category.find('a',{'class' : 'food-search-result-name'}, href = True)
            if optimizedLink:
                link_to_data = optimizedLink['href']
                #print quantity + ' of ' + ingredient + ': ' + link_to_data
                #print 'found'
                break
        elif i == 1 and (keywords[i] in subCategory.lower() and keywords[0] in subCategory.lower()):
            optimizedLink = category.find('a',{'class' : 'food-search-result-name'}, href = True)
            if optimizedLink:
                link_to_data = optimizedLink['href']
                #print quantity + ' of ' + ingredient + ': ' + link_to_data
                #print 'found'
                break
        elif i == 2 and (keywords[i] in subCategory.lower() or keywords[1] in subCategory.lower() or keywords[0] in subCategory.lower()):
            optimizedLink = category.find('a',{'class' : 'food-search-result-name'}, href = True)
            if optimizedLink:
                link_to_data = optimizedLink['href']
                #print quantity + ' of ' + ingredient + ': ' + link_to_data
                #print 'found'
                break
    #intellegent search, checks if there is a link in green category with all keywords in it
    if link_to_data == ' ':#if havent found link yet
        for category in soup.find_all('div', {'class' : 'food-search-result left-vertical-border-green'}):
            link = category.find('a',{'class' : 'food-search-result-name'}, href = True)
            if len(keywords) == 3:
                if '+' not in link['href'] and keywords[0] in link['href'] and keywords[1] in link['href'] and keywords[0] in link['href']:
                    #print quantity + ' of ' + ingredient + ': ' + link['href']
                    link_to_data = link['href']
                    break
            elif len(keywords) == 2:
                if '+' not in link['href'] and keywords[0] in link['href'] and keywords[1] in link['href']:
                    #print quantity + ' of ' + ingredient + ': ' + link['href']
                    link_to_data = link['href']
                    break
            elif len(keywords) == 1:
                if '+' not in link['href'] and keywords[0] in link['href']:
                    #print quantity + ' of ' + ingredient + ': ' + link['href']
                    link_to_data = link['href']
                    break
    #least intellegent search, goes through all the links
    if(link_to_data == ' '):#if no link found yet
        for link in soup.find_all('a', href = True):
            if len(keywords) == 3:
                if '+' not in link['href'] and keywords[0] in link['href'] and keywords[1] in link['href'] and keywords[0] in link['href']:
                    #print quantity + ' of ' + ingredient + ': ' + link['href']
                    link_to_data = link['href']
                    break
            elif len(keywords) == 2:
                if '+' not in link['href'] and keywords[0] in link['href'] and keywords[1] in link['href']:
                    #print quantity + ' of ' + ingredient + ': ' + link['href']
                    link_to_data = link['href']
                    break
            elif len(keywords) == 1:
                if '+' not in link['href'] and keywords[0] in link['href']:
                    #print quantity + ' of ' + ingredient + ': ' + link['href']
                    link_to_data = link['href']
                    break

    r.close()
    return link_to_data
