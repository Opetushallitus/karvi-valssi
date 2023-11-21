import styles from './TemplateName.module.css';

interface TemplateNameProps {}

function TemplateName(props: TemplateNameProps) {
    return (
        <div className={styles.TemplateName} data-testid="TemplateName">
            <h1>TemplateName component</h1>
            {props[0]}
        </div>
    );
}

export default TemplateName;
