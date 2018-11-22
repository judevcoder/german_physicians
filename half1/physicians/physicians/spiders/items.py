# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class PhysiciansItem(Item):
    URL = Field()
    GeneratedID = Field()
    SitePrimaryKey = Field()
    ListType = Field()
    Fullname = Field()
    FirstName = Field()
    LastName = Field()
    StateName = Field()
    LANR = Field()
    remarks = Field()


class SpecialtiesItem(Item):
    PhysicianPrimaryID = Field()
    SpecialtyName = Field()


class LocationsItem(Item):
    LocationID = Field()
    PageURL = Field()
    Name = Field()
    PhysicianID = Field()
    Address = Field()
    State = Field()
    # Street = Field()
    # Number = Field()
    # City = Field()
    email = Field()
    Phone = Field()
    Website = Field()
    BSNR = Field()
    HBSNR = Field()
    GMaps_link = Field()
