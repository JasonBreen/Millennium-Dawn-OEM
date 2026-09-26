import type { Root } from "mdast";
import { visit } from "unist-util-visit";
import type { Parent } from "unist";

type TextDirectiveNode = Parent & {
  type: "textDirective";
  name?: string;
  attributes?: Record<string, string | null>;
  data?: Record<string, unknown>;
};

const ROLE_KINDS = new Set(["junior", "developer", "senior", "inactive", "council"]);

export function remarkDevTeamRoles(): (tree: Root) => void {
  return (tree: Root): void => {
    visit(tree, (node) => {
      if (node.type !== "textDirective") return;

      const directiveNode = node as TextDirectiveNode;
      if (directiveNode.name !== "role") return;

      const kind = directiveNode.attributes?.kind;
      if (!kind || !ROLE_KINDS.has(kind)) return;

      const data = (directiveNode.data ??= {});
      data.hName = "span";
      data.hProperties = { className: ["dev-team-role", `dev-team-role--${kind}`] };
    });
  };
}
