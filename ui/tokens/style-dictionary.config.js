export default {
  source: ["tokens/design-tokens.json"],
  usesDtcg: true,
  hooks: {
    formats: {
      "velodex/tailwind-theme": ({ dictionary }) => {
        const colors = [];
        const shadows = [];

        for (const token of dictionary.allTokens) {
          const [category, ...rest] = token.path;
          const name = rest.join("-");
          const value = token.$value;

          if (category === "color") {
            colors.push(`  --color-${name}: ${value};`);
          } else if (category === "shadow") {
            shadows.push(`  --shadow-${name}: ${value};`);
          }
        }

        return [
          "/* AUTO-GENERATED — do not edit. Run: npm run tokens */",
          "@theme {",
          "  /* Colors */",
          ...colors,
          "  /* Shadows */",
          ...shadows,
          "}",
          "",
        ].join("\n");
      },
    },
  },
  platforms: {
    css: {
      buildPath: "tokens/generated/",
      files: [
        {
          destination: "tokens.css",
          format: "velodex/tailwind-theme",
        },
      ],
    },
  },
};
