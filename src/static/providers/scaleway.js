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
    browseUrl: function() {
        return "https://github.com/" + this.repo + "/blob/main/";
    },
};
