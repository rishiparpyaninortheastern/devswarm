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
  description = "Azure subscription GUID; provide only when reviewing a deployment plan."
  type        = string
  validation {
    condition     = can(regex("^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$", var.subscription_id))
    error_message = "subscription_id must be an Azure subscription GUID."
  }
}
variable "location" {
  type    = string
  default = "eastus2"
}
variable "prefix" {
  description = "Unique deployment prefix: 3-20 lowercase letters/digits/hyphens; start with a letter and end with a letter/digit."
  type        = string
  default     = "devswarm"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,18}[a-z0-9]$", var.prefix))
    error_message = "prefix must be 3-20 lowercase characters, start with a letter and end with a letter or digit."
  }
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
