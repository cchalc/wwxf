#!/bin/sh

az storage blob upload-batch --destination bronze --account-name dltp8tdylpblob --destination-path fire_weather_forecast --source fire_weather_forecast_zones

az storage blob upload-batch --destination bronze --account-name dltp8tdylpblob --destination-path rdps_pr --source rdps_pr

az storage blob upload-batch --destination bronze --account-name dltp8tdylpblob --destination-path rdps_tt --source rdps_tt

az storage blob upload-batch --destination bronze --account-name dltp8tdylpblob --destination-path weather_station --source weather_station
