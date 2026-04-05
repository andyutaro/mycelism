import { QuartzComponent, QuartzComponentConstructor } from "../types"
import { classNames } from "../../util/lang"
import { htmlToJsx } from "../../util/jsx"

const Content: QuartzComponent = ({ fileData, tree }) => {
  const content = htmlToJsx(fileData.filePath ?? "", tree)
  const classes = fileData.frontmatter?.cssclasses ?? []

  return <article className={classNames("popover-hint", "content", ...classes)}>{content}</article>
}

export default (() => Content) satisfies QuartzComponentConstructor
