terraform {
  required_version = ">= 1.9, < 2.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.38"
    }
  }
}
provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
variable "subscription_id" {
  type = string
}
variable "location" {
  type    = string
  default = "eastus2"
}
variable "prefix" {
  type    = string
  default = "devswarm"
}
resource "azurerm_resource_group" "main" {
  name     = "${var.prefix}-dev-rg"
  location = var.location
}
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.prefix}-logs"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}
resource "azurerm_container_app_environment" "main" {
  name                       = "${var.prefix}-env"
  location                   = var.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
}
resource "azurerm_servicebus_namespace" "main" {
  name                = "${var.prefix}-events"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Standard"
  minimum_tls_version = "1.2"
  local_auth_enabled  = false
}
resource "azurerm_servicebus_queue" "incidents" {
  name                                    = "incidents"
  namespace_id                            = azurerm_servicebus_namespace.main.id
  requires_duplicate_detection            = true
  duplicate_detection_history_time_window = "PT10M"
  max_delivery_count                      = 5
}
resource "azurerm_user_assigned_identity" "runtime" {
  name                = "${var.prefix}-runtime"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
}
output "resource_group" {
  value = azurerm_resource_group.main.name
}
