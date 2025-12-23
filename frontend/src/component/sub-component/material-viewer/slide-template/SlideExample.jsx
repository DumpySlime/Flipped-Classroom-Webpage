import '../../../../styles.css';
import '../../../../dashboard.css';

/*  slide: {subtitle: conclusion,
            content: conclusion point form,
            slide_type: explanation,
            page:4} */
function SlideExample ({ slide }) {
  // Process the content to ensuree it's in cluster format
  const contentArray = Array.isArray(slide.content) ? slide.content : [slide.content];
  
  // title as the first line
  const question = contentArray[0] || '';
  
  // remaining lines as solution steps
  const solutionSteps = contentArray.slice(1);
  
  return (
    <div className="slide-example">
      <h1>{slide.subtitle}</h1>
      <div className="example-body">
        <div className="example-left">
          <h2>Question</h2>
          <p>{question}</p>
        </div>
        <div className="example-right">
          <h2>Solution</h2>
          <ul>
            {solutionSteps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ul>
        </div>
      </div>
      <div className="slide-footer">
        <p>Page {slide.page}</p>
      </div>
    </div>
  );
}

export default SlideExample;
