.PHONY: update-charter

update-charter: ## dev-charter を最新版に更新
	CHARTER_UPDATE_ONLY=1 bash <(curl -fsSL https://raw.githubusercontent.com/y-marui/dev-charter/main/scripts/install.sh)
