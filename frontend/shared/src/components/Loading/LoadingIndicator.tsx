import {useObservable} from 'rxjs-hooks';
import Spinner from 'react-spinners/HashLoader';
import LoadingService from '../../services/Loading/Loading-service';
import styles from './LoadingIndicator.module.css';

interface LoadingIndicatorProps {
    alwaysLoading?: boolean;
}

function LoadingIndicator({alwaysLoading = false}: LoadingIndicatorProps) {
    const isLoading = useObservable(() => LoadingService.isLoading$);
    return alwaysLoading || isLoading ? (
        <div className={styles.LoadingIndicator} data-testid="LoadingIndicator">
            <Spinner color="green" />
        </div>
    ) : null;
}

export default LoadingIndicator;
