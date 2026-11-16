// Optional macOS review aid: emit JSON of OCR lines from selected cached, scanned municipal minutes.
import Foundation
import AppKit
import PDFKit
import Vision
let input = URL(fileURLWithPath:CommandLine.arguments[1]); let limit = Int(CommandLine.arguments[2])!
let doc = PDFDocument(url:input)!; var output = [[String]]()
for n in 0..<min(limit, doc.pageCount) {
    let page=doc.page(at:n)!; let img=page.thumbnail(of:NSSize(width:1650,height:2200),for:.mediaBox)
    var rect=NSRect(origin:.zero,size:img.size)
    let cg=img.cgImage(forProposedRect:&rect,context:nil,hints:nil)!
    let req=VNRecognizeTextRequest(); req.recognitionLevel = .accurate; req.usesLanguageCorrection=false
    try VNImageRequestHandler(cgImage:cg).perform([req])
    output.append((req.results ?? []).compactMap{$0.topCandidates(1).first?.string})
}
FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject:output))
