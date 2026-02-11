const PROVIDER = {
    name: "Scaleway",
    repo: "lejeunen/scaleway-starter-kit",
    repoUrl: function() {
        return "https://github.com/" + this.repo;
    },
    complianceUrl: function(lang) {
        const suffix = lang === "fr" ? ".fr" : "";
        return "https://raw.githubusercontent.com/" + this.repo + "/main/COMPLIANCE" + suffix + ".md";
    },
    whySovereignUrl: function(lang) {
        const suffix = lang === "fr" ? ".fr" : "";
        return "https://raw.githubusercontent.com/" + this.repo + "/main/WHY-SOVEREIGN-CLOUD" + suffix + ".md";
    },
    readmeUrl: function() {
        return "https://raw.githubusercontent.com/" + this.repo + "/main/README.md";
    },
    browseUrl: function() {
        return "https://github.com/" + this.repo + "/blob/main/";
    },
};
