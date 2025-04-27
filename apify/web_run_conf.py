def conf():
    return rf"""
{{
    "aggressivePrune": false,
    "clickElementsCssSelector": "[aria-expanded=\"false\"]",
    "clientSideMinChangePercentage": 15,
    "debugLog": false,
    "debugMode": false,
    "expandIframes": true,
    "ignoreCanonicalUrl": false,
    "includeUrls": [
        "https://github.com/google/deepvariant/.*"
    ],
    "keepUrlFragments": false,
    "linkSelector": "a[href]",
    "maxDepth": 30,
    "proxyConfiguration": {{
        "useApifyProxy": true
    }},
    "readableTextCharThreshold": 100,
    "removeCookieWarnings": true,
    "removeElementsCssSelector": "nav, footer, script, style, noscript, svg,\n[role=\"alert\"],\n[role=\"banner\"],\n[role=\"dialog\"],\n[role=\"alertdialog\"],\n[role=\"region\"][aria-label*=\"skip\" i],\n[aria-modal=\"true\"]",
    "renderingTypeDetectionPercentage": 10,
    "saveFiles": false,
    "saveHtml": false,
    "saveHtmlAsFile": false,
    "saveMarkdown": true,
    "saveScreenshots": false,
    "startUrls": [
        {{
            "url": "https://github.com/google/deepvariant/",
            "method": "GET"
        }}
    ],
    "useSitemaps": false
}}

"""